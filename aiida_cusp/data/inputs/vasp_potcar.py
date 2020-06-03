# -*- coding: utf-8 -*-


"""
Datatypes and methods to initialize and interact with VASP specific
pseudo-potential files
"""


import re

from pymatgen.core import periodic_table
from aiida.orm import SinglefileData, Dict, QueryBuilder

from aiida_cusp.utils.defaults import VaspDefaults
from aiida_cusp.utils import PotcarParser
from aiida_cusp.utils.exceptions import (VaspPotcarFileError,
                                         MultiplePotcarError)


class VaspPotcarFile(SinglefileData):
    """
    Datatype representing an actual POTCAR file object stored to
    the AiiDA database.

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
        # check if path points to file
        if not path_to_potcar.is_file():
            raise VaspPotcarFileError("The passed path '{}' does not seem "
                                      "to point to a valid POTCAR file"
                                      .format(str(path_to_potcar)))
        # check if file is named POTCAR
        if not path_to_potcar.name == VaspDefaults.FNAMES['potcar']:
            raise VaspPotcarFileError("Expected pseudo-potential file "
                                      "named POTCAR, got '{}'"
                                      .format(str(path_to_potcar.name)))
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
            raise VaspPotcarFileError("Database query for potcat file nodes "
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
    potential's hash value and the unique potential identifiers (name,
    functional and version)
    """
    pass
