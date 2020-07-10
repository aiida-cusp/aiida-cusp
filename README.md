# aiida-cusp - a Custodian based VASP Plugin for AiiDA
[![Documentation Status](https://readthedocs.org/projects/aiida-cusp/badge/?version=latest)](https://aiida-cusp.readthedocs.io/en/latest/?badge=latest)
[![tests](https://github.com/aiida-cusp/aiida-cusp/workflows/tests/badge.svg?branch=develop)](https://github.com/aiida-cusp/aiida-cusp/actions)
[![codecov](https://codecov.io/gh/aiida-cusp/aiida-cusp/branch/develop/graph/badge.svg)](https://codecov.io/gh/aiida-cusp/aiida-cusp)

[Custodian](https://materialsproject.github.io/custodian) plugin for VASP enabling automated error correction for [AiiDA](https://www.aiida.net) managed VASP calculations

## Highlights

* Automated error corrections for VASP calculations on the calculation's runtime level (rather than on the workflow level)
* Full compatability with [pymatgen](https://pymatgen.org) and easy access to set of therein implemented tools for pre- and postprocessing of VASP calculations directly from the implemented datatypes
* It' still VASP, but better!

## Contributing

Suggestions for useful improvements, feature requests, bug reports and the like are highly welcome and appreciated.
Especially the contribution of new workflows that were developed based on this plugin is highly encouraged to transform this plugin into a powerful tool for the scientific community.

### Bug Reports
If you think you found a bug feel free to open an issue on the plugin's [GitHub repository](https://github.com/astamminger/aiida-cusp/issues).

### Adding new Features and Changes
For changes you would like to add to the plugin please refer to the [`CONTRIBUTING.md`](CONTRIBUTING.md) file located in the repository root.

## License

The `aiida-cusp` plugin for AiiDA is distributed as free and open-source software (FOSS) licensed under the MIT open-source license (see [`LICENSE`](LICENSE)).
