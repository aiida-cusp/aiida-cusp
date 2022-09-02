# -*- coding: utf-8 -*-


"""
Datatypes and methods to initialize and interact with VASP specific
pseudo-potential files
"""


import re

from pymatgen.core import Structure, periodic_table
from pymatgen.io.vasp.inputs import Poscar, Potcar, PotcarSingle
from aiida.orm import (SinglefileData, Dict, QueryBuilder, load_node,
                       StructureData)
from aiida.common.exceptions import NotExistent

from aiida_cusp.utils.defaults import VaspDefaults
from aiida_cusp.data.inputs.vasp_poscar import VaspPoscarData
from aiida_cusp.utils import PotcarParser
from aiida_cusp.utils.exceptions import (VaspPotcarFileError,
                                         VaspPotcarDataError,
                                         MultiplePotcarError)


# FIXME: Add test for the potcar_from_linklist() classmethod of the
#        VaspPotcarData-calss
# FIXME: Allow the user defined potcar_props to be of type list containing
#        the potential names only. this would make the method fully compatible
#        with pymatgen sets (but first check if we can uniquely identify the
#        element name from the given potential name


class VaspPotcarFile(SinglefileData):
    """
    Datatype representing an actual POTCAR file object stored to
    the AiiDA database.

    Note that this class should never be called directly to add any
    pseudo-potentials to the database but always using the provided
    add_potential()-classmethod.

    :param path_to_potcar: Absolute path pointing to the potcar file
    :type path_to_potcar: str
    :param name: qualified name of the potential at location
        `path_to_potcar` (i.e. Li, Li_sv, Ge_pv_GW, ...)
    :type name: str
    :param element: element associated with the pseudo-potential
    :type element: str
    :param version: version of the pseudo-potential, i.e. the creation
        date as 8-digit integer in numerical YYYYMMDD representation
    :type version: int
    :param functional: functional group of the potential located at
        `path_to_potcar`. Valid choices are: lda_us, lda, lda_52, lda_54,
        pbe, pbe_52, pbe_54, pw91 and pw91_us
    :type functional: str
    :param checksum: SHA-256 hash of the potential contents
    :type checksum: str
    """
    def __init__(self, path_to_potcar, name, element, version, functional,
                 checksum):
        # initialize the bare SinglefileData node
        super(VaspPotcarFile, self).__init__(file=str(path_to_potcar))
        # populate the generated node with potential identifiers
        self.set_attribute('name', name)
        self.set_attribute('hash', checksum)
        self.set_attribute('element', element)
        self.set_attribute('version', version)
        self.set_attribute('functional', functional)
        # fail early if one of the attributes is faulty
        self.validate_name(name)
        self.validate_version(version)
        self.validate_element(element)
        self.validate_functional(functional)

    @property
    def name(self):
        return self.get_attribute('name')

    @property
    def hash(self):
        return self.get_attribute('hash')

    @property
    def element(self):
        return self.get_attribute('element')

    @property
    def version(self):
        return self.get_attribute('version')

    @property
    def functional(self):
        return self.get_attribute('functional')

    @classmethod
    def add_potential(cls, path_to_potcar, name=None, functional=None):
        """
        Create and return unstored potential node from POTCAR file.

        Loads the POTCAR file at the given location and parses the basic
        identifiers from the file's contents.

        :param path_to_potcar: absolute path pointing to a potcar file
        :type path_to_potcar: pathlib.Path
        :param name: qualified name of the potential at location
            `path_to_potcar` (i.e. Li, Li_sv, Ge_pv_GW, ...)
        :type name: str
        :param functional: functional group of the potential located at
            `path_to_potcar`. Valid choices are: lda_us, lda, lda_52, lda_54,
            pbe, pbe_52, pbe_54, pw91 and pw91_us
        :type functional: str
        """
        # initialize the new VaspPotcarFile node
        parsed = PotcarParser(path_to_potcar, name=name, functional=functional)
        if cls.is_unique(parsed):  # this will raise if not unique!
            potential_node = cls(str(path_to_potcar.absolute()),
                                 name=parsed.name, element=parsed.element,
                                 version=parsed.version,
                                 functional=parsed.functional.lower(),
                                 checksum=parsed.hash)
            return potential_node

    @classmethod
    def is_unique(cls, potcar_attrs):
        """
        Check if a potential is unqiue (i.e. not already stored).

        Uniqueness is checked based on the unique potential identifiers, i.e.
        the potential name, it's version and the associated functional.

        :param potcar_attrs: a PotcarParser instance of the potential to be
            checked for uniqueness
        :type potcar_attrs: :class:`aiida_cusp.utils.PotcarParser`
        :return: `True` if no other potential with identical identifiers exists
            in the database
        :rtype: `bool`
        :raises MultiplePotcarError: if the a potential with identical
            identifiers is already stored in the database
        """
        # get identifiers from PotcarParser instance and query the database
        # for potentials sharing these identifiers
        potcar_name = potcar_attrs.name
        potcar_functional = potcar_attrs.functional
        potcar_version = potcar_attrs.version
        potcar_hash = potcar_attrs.hash
        potentials_with_tags = cls.from_tags(name=potcar_name,
                                             version=potcar_version,
                                             functional=potcar_functional)
        if len(potentials_with_tags) == 0:
            return True  # potential is unique
        else:
            first_match = potentials_with_tags[0]
            if first_match.hash == potcar_hash:  # it's the very same potential
                err_msg = ("Identical potential (same identifiers and "
                           "identical hash value) is already present in the "
                           "database at PK: {}".format(first_match.pk))
            else:  # same identifiers but different contents?
                err_msg = ("Potential with matching identifiers ({}, {}, {}) "
                           "but different hash value is already present in "
                           "the database at PK: {}. (This usually means that "
                           "both potentials share the same identifiers but "
                           "have different contents. If you know what you're "
                           "doing carefully check the potential contents and "
                           "change the potential identifiers in order to "
                           "store the potential)"
                           .format(potcar_name, potcar_version,
                                   potcar_functional, first_match.pk))
            raise MultiplePotcarError(err_msg)

    @classmethod
    def from_tags(cls, name=None, element=None, version=None, functional=None,
                  checksum=None):
        """
        Query database for potentials containing a set of given tags.

        To query the database at least one of the available tags has to be
        given. If multiple tags are defined only potentials matching **all**
        of the defined tags will be returned.

        :param name: fully qualified name of the potential (i.e. Li_sv, Li,
            Ge_sv_GW, P, ...)
        :type name: str
        :param element: name of the element associated with a given potential
            (i.e. Cl, Li, S, ...)
        :type element: str
        :param version: version (i.e. the creation date) of the potential in
            numerical 8-digit integer YYYYMMDD representation
        :type version: int
        :param functional: functional filter to query only for potentials
            associated with a specific functional. Allowed values are: lda_us,
            lda, lda_52, lda_54, pbe, pbe_52, pbe_54, pw91 and pw91_us
        :type functional: str
        :param checksum: the SHA-256 hash value associated with the contents
            of a potcar file
        :type hash: str
        :return: a list of :class:`VaspPotcarFile` nodes in the database
            matching the given tags
        :rtype: list(:class:`VaspPotcarFile`)
        """
        # build the filters for the database query
        filters = {}
        if name is not None:
            filters.update({'attributes.name': {'==': name}})
        if element is not None:
            filters.update({'attributes.element': {'==': element}})
        if version is not None:
            filters.update({'attributes.version': {'==': version}})
        if checksum is not None:
            filters.update({'attributes.hash': {'==': checksum}})
        if functional is not None:
            filters.update({'attributes.functional': {'==': functional}})
        # setup query for VaspPotcarFile objects with generated filter list
        if filters:
            database_potential_query = QueryBuilder()
            database_potential_query.append(cls, filters=filters)
        else:
            raise VaspPotcarFileError("Database query for potcar file nodes "
                                      "failed because not tags were given")
        # return results obtained by the query builder
        return [_ for [_] in database_potential_query.all()]

    def _validate(self):
        """Validate the stored potential identifiers."""
        # run validation provided by parent SinglefileData class
        super(VaspPotcarFile, self)._validate()
        # validate additionally defined potential attributes
        element = self.get_attribute('element')
        name = self.get_attribute('name')
        version = self.get_attribute('version')
        functional = self.get_attribute('functional')

    def validate_element(self, element):
        """Assert the given element is in the list of elements."""
        elements = [e.name for e in periodic_table.Element]
        if element not in elements:
            raise VaspPotcarFileError("Found invalid element name '{}'"
                                      .format(element))

    def validate_name(self, name):
        """Assert potential name starts with valid element name."""
        match_name = re.match(r"^[A-Z]{1}[a-z]{0,1}", name)
        if match_name is None:
            raise VaspPotcarFileError("Unable to parse the element from given "
                                      "potential name '{}'".format(name))
        else:
            elements = [e.name for e in periodic_table.Element]
            if match_name.group() not in elements:
                raise VaspPotcarFileError("Element '{}' parsed from potential "
                                          "name '{}' not a valid element name"
                                          .format(match_name.group(), name))

    def validate_version(self, version):
        """Assert the parsed potential version is valid."""
        # potential version is generated from the potential's creation date
        # and transformed into a numerical 8-digit YYYYMMDD representation.
        # Thus, each potential's version is expected to be greater than or
        # equal to 10000101
        if version < 10000101:
            raise VaspPotcarFileError("Potential version '{}' does not "
                                      "correspond to the expected YYYYMMDD "
                                      "format".format(version))

    def validate_functional(self, functional):
        """Assert the functional is in the list of valid functionals."""
        valid_functionals = list(VaspDefaults.FUNCTIONAL_MAP.values())
        if functional not in valid_functionals:
            valid_funcs = ", ".join(valid_functionals)
            raise VaspPotcarFileError("Given potential functional '{}' is not "
                                      "in the list of valid functionals ({})"
                                      .format(functional, valid_funcs))


class VaspPotcarData(Dict):
    """
    Pseudopotential input datatype for VASP calculations.

    Contrary to the related VaspPotcarFile class this object does **not**
    contain any proprietary potential information and only stores the
    potential's uuid value and the unique potential identifiers (name,
    functional, version and the content hash)
    """
    def __init__(self, *args, **kwargs):
        name = kwargs.pop('name', None)
        version = kwargs.pop('version', None)
        functional = kwargs.pop('functional', None)
        if not any([name, version, functional]):
            super(VaspPotcarData, self).__init__(*args, **kwargs)
        else:  # redirect to initialization from tags
            self.init_from_tags(name, version, functional)

    def init_from_tags(self, name, version, functional):
        """
        Initialized VaspPotcarData node from given potential tags

        :param name: name of the potential
        :type name: `str`
        :param version: version of the potential
        :type version: `int`
        :param functional: functional of the potential
        :type functional: `str`
        :raises VaspPotcarDataError: if one of the non-optional parameters
            name, version or functional is missing
        """
        # check parameters are complete
        if name is None:
            raise VaspPotcarDataError("Missing non-optional argument "
                                      "'name'")
        if version is None:
            raise VaspPotcarDataError("Missing non-optional argument "
                                      "'version'")
        if functional is None:
            raise VaspPotcarDataError("Missing non-optional argument "
                                      "'functional'")
        potentials = VaspPotcarFile.from_tags(name=name, version=version,
                                              functional=functional)
        if len(potentials) == 0:
            raise VaspPotcarDataError("Unable to initialize VaspPotcarData "
                                      "since no potential was found for the "
                                      "given identifiers (name: {}, version: "
                                      "{}, functional: {})"
                                      .format(name, version, functional))
        # define potential contents to be stored with the VaspPotcarData node
        contents = {
            'name': potentials[0].name,
            'version': potentials[0].version,
            'element': potentials[0].element,
            'functional': potentials[0].functional,
            'filenode_uuid': potentials[0].uuid,
            'hash': potentials[0].hash,
        }
        # add a label to the node
        label = u'{} {} (v{})'.format(contents['name'], contents['functional'],
                                      contents['version'])
        super(VaspPotcarData, self).__init__(dict=contents, label=label)

    @classmethod
    def from_structure(cls, structure, functional, potcar_params={}):
        """
        Create potcar input data for a given structure and functional.

        Reads elements present in the passed structure and builds the input
        list of VaspPotcarData instances defining the potentials to be used
        for each element. By default the potential names are assumed to equal
        the corresponding element names and potentials of the latest version
        are used. This default behavior can be changed on a per element basis
        by using the `potcar_params` dictionary to explicitly define the
        potential name and / or version to be used for a given element

        Assume a structure containig elements 'A' and 'B'. For both elements
        the potentials with name 'A_pv' and 'B_pv' should be used and
        additionally element 'B' requires the use of a specific potential
        version, i.e. version 10000101 (Note that the version number is simply
        an integer representation of the creation date found in the potcar
        files title in the format YYYYMMDD) The above can be achived by
        passing the following `potcar_params` to the method:

        .. code-block:: python

            potcar_params = {
                'A': {'name': 'A_pv'},
                'B': {'name': 'B_pv', 'version': 10000101},
            }

        .. note::

           Alternatively it is also possible to use the `potcar_params` to
           pass a simple list defining the potential names (i.e. A_pv, B_pv,
           ...) to be used for the calculation (for all elements in the
           structure not defined by the passed list the default potentials
           will be used!) In that case potentials of the latest version are
           used and the method tries to figure out the elements corresponding
           to the potential name automatically. Because of that: make sure
           that each potential name starts with the corresponding element name
           (**case sensitive!**) followed by any non-letter character,
           for instance:
           **Ge**\ _d_GW, **Li**\ _sv, **Cu**, **H**\ 1.75, etc...

        :param structure: input structure for which the potential list is
            generated
        :type structure: :class:`~pymatgen.core.structure.Structure`,
            :class:`~pymatgen.io.vasp.inputs.Poscar`,
            :class:`~aiida.orm.nodes.data.structure.StructureData` or
            :class:`~aiida_cusp.data.inputs.vasp_poscar.VaspPoscarData`
        :param functional: functional type of the used potentials, accepted
            functionals inputs are: `'lda_us'`, `'lda'`, `'lda_52'`, `'pbe'`,
            `'pbe_52'`, `'pbe_54'`, `'pw91_us'` and `'pw91'`.
        :type functional: `str`
        :param potcar_params: optional dictionary overriding the default
            potential name and version used for the element given as key or
            a list of potential names to be used for the calculation
        :type potcar_params: `dict` or `list`
        """  # noqa: W605
        # get pymatgen structure object
        if isinstance(structure, Structure):
            struct = structure
        elif isinstance(structure, StructureData):
            struct = structure.get_pymatgen_structure()
        elif isinstance(structure, Poscar):
            struct = structure.structure
        elif isinstance(structure, VaspPoscarData):
            struct = structure.get_poscar().structure
        else:
            raise VaspPotcarDataError("Unsupported structure type '{}'"
                                      .format(type(structure)))
        # transform list of potential names to valid potential params
        # dictionary
        if isinstance(potcar_params, (list, tuple)):
            potcar_params = cls.potcar_props_from_name_list(potcar_params)
        # build list of species comprising the structure and create default
        # potential properties based on the species list (use a set because
        # of possibly non-ordered input structures)
        symbols = list(set([str(element) for element in struct.species]))
        potcar_props_defaults = {
            symbol: {'name': symbol, 'version': None} for symbol in symbols
        }
        # update pot_props_defaults with potential settings defined by the user
        # and query for matching potentials
        element_potential_map = {}
        for element, potcar_props in potcar_props_defaults.items():
            user_props = potcar_params.get(element, {})
            potcar_props.update(user_props, functional=functional.lower())
            potentials = VaspPotcarFile.from_tags(**potcar_props)
            # in case multiple potentials are found due to unset version
            potential = sorted(potentials, key=lambda potcar: potcar.version,
                               reverse=True)[0]
            identifiers = {
                'name': potential.name,
                'functional': potential.functional,
                'version': potential.version,
            }
            element_potential_map.update({element: cls(**identifiers)})
        return element_potential_map

    @classmethod
    def potcar_props_from_name_list(cls, potcar_name_list):
        """
        Create a valid potcar properties dictionary from a list of given
        potential names
        """
        valid_elements = [e.name for e in periodic_table.Element]
        element_regex = r"^([A-Z]{1}[a-z]*)(?=[^A-Za-z]*)"
        elements, names = [], []
        for potential_name in potcar_name_list:
            element_match = re.match(element_regex, potential_name)
            if element_match is None:
                raise VaspPotcarDataError("Couldn't parse the element name "
                                          "for the passed potential name '{}'"
                                          .format(potential_name))
            parsed_element = element_match.group(0)
            if parsed_element not in valid_elements:
                raise VaspPotcarDataError("Parsed element '{}' is not in the "
                                          "list of valid elements"
                                          .format(parsed_element))
            elements.append(parsed_element)
            names.append({'name': potential_name})
        # finally check that potentials for each element are only defined once
        if len(elements) != len(set(elements)):
            raise VaspPotcarDataError("Multiple potential names given for the "
                                      "same element")
        return dict(zip(elements, names))

    @classmethod
    def potcar_from_linklist(cls, poscar_data, linklist):
        """
        Assemble pymatgen Potcar object from a list of VaspPotcarData instances

        Reads pseudo-potential from the passed list connecting each element
        with it's potential and creates the complete Potcar file according
        to the element ordering fodun in the passed poscar data object.

        :param poscar_data: input structure for VASP calculations
        :type poscar: :class:`aiida_cusp.data.inputs.VaspPoscarData`
        :param linklist: dictionary mapping element names to VaspPotcarData
            instances
        :type linklist: `dict`
        :returns: pymatgen Potcar data instance with containing the
            concatenated pseudo-potential information for all elements defined
            in the linklist
        :rtype: :class:`~pymatgen.io.vasp.inputs.Potcar`
        """
        # initialize empty Potcar object
        complete_potcar = Potcar()
        # file empty potcar with potential in order of elements found in the
        # passed structure data
        site_symbols = poscar_data.get_poscar().site_symbols
        for site_symbol in site_symbols:
            try:
                potential_pointer = linklist[site_symbol]
            except KeyError:
                raise VaspPotcarDataError("Found no potential in passed "
                                          "potential-element map for "
                                          "site symbol '{}'"
                                          .format(site_symbol))
            potential_file = potential_pointer.load_potential_file_node()
            potential_contents = potential_file.get_content()
            potcar_single = PotcarSingle(potential_contents)
            complete_potcar.append(potcar_single)
        return complete_potcar

    @property
    def name(self):
        """Make associated potential name a property"""
        return self.dict['name']

    @property
    def functional(self):
        """Make associated potential functional a property"""
        return self.dict['functional']

    @property
    def version(self):
        """Make associated potential version a property"""
        return self.dict['version']

    @property
    def filenode_uuid(self):
        """Make associated potential UUID a property"""
        return self.dict['filenode_uuid']

    @property
    def element(self):
        """Make associated potential element a property"""
        return self.dict['element']

    @property
    def hash(self):
        """Make associated potential hash a property"""
        return self.dict['hash']

    def load_potential_file_node(self):
        """
        Load the actual potential node associated with the potential data node

        First tries to load the potential file node from the given UUID. If
        this fails (for instance because the VaspPotcarData node was imported
        from some other database) a second attempt will try to load a potential
        file node based on the stored content hash.

        :returns: the associated VaspPotcarFile node
        :rtype: :class:`~aiida_cusp.data.inputs.vasp_potcar.VaspPotcarFile`
        :raises VaspPotcarDataError: if no corresponding potential file node
            is found in the database
        """
        contents = self.get_dict()
        try:
            try:  # first attempt: try to load from uuid
                uuid = contents['filenode_uuid']
                loaded_file_node = load_node(uuid)
            except NotExistent:  # second attemt: try to load from hash
                chksum = contents['hash']
                loaded_file_node = VaspPotcarFile.from_tags(checksum=chksum)[0]
        except IndexError:
            raise VaspPotcarDataError("Unable to discover associated "
                                      "potential file node in the database "
                                      "(tried UUID and HASH). Check if "
                                      "potential is available!")
        # sanity check if the loaded potential really matches
        assert loaded_file_node.name == contents['name']
        assert loaded_file_node.version == contents['version']
        assert loaded_file_node.functional == contents['functional']
        assert loaded_file_node.element == contents['element']
        assert loaded_file_node.hash == contents['hash']
        # return the discovered file
        return loaded_file_node
