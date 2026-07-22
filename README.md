# OpenHCS Napari ROI Manager

[![License BSD-3](https://img.shields.io/pypi/l/openhcs-napari-roi-manager.svg?color=green)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/openhcs-napari-roi-manager.svg?color=green)](https://pypi.org/project/openhcs-napari-roi-manager)
[![Python Version](https://img.shields.io/pypi/pyversions/openhcs-napari-roi-manager.svg?color=green)](https://python.org)
[![tests](https://github.com/OpenHCSDev/openhcs-napari-roi-manager/actions/workflows/test_and_deploy.yml/badge.svg)](https://github.com/OpenHCSDev/openhcs-napari-roi-manager/actions)

An OpenHCS-maintained Napari ROI Manager with a Fiji/ImageJ-style workflow.

This project is a BSD-licensed fork of Hanjin Liu's
[napari-roi-manager](https://github.com/hanjinliu/napari-roi-manager). The
original copyright, license, and Git history are retained. The OpenHCS fork
replaces the private custom Shapes subclass with direct binding to Napari's
native `Shapes` owner.

![](https://github.com/hanjinliu/napari-roi-manager/blob/main/images/demo.gif)

&check; Binds directly to the active native Shapes layer, so geometry, features,
selection, dimensionality, and lifecycle remain compatible with every other plugin.

&check; Supports importing and exporting ImageJ ROI files.

&check; Preserves Fiji-style Add, Remove, Rename, Specify, Load, Save, Show All,
and row-selection workflows without a hidden copy of the ROI geometry.

----------------------------------

The upstream [napari] plugin was generated with [Cookiecutter] using
[@napari]'s [cookiecutter-napari-plugin] template.


## Installation

Install the OpenHCS-owned distribution via [pip]:

    pip install openhcs-napari-roi-manager


## Usage

Open **Plugins > OpenHCS ROI Manager** while a Shapes layer is active. The
manager lists and edits that exact layer; opening the widget does not create
another layer.
Selecting a row updates the native Shapes selection, and selecting ROIs in the
viewer updates the table.

Use **New Set** when you explicitly want a new empty Shapes layer. **Load** can
also create a layer when no Shapes layer is active. Multidimensional coordinates
are retained in JSON ROI sets and mapped to ImageJ position, time, and z fields
when ImageJ ROI files are used.



To install the latest development version:

    pip install git+https://github.com/OpenHCSDev/openhcs-napari-roi-manager.git


## Contributing

Contributions are very welcome. Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request.

## License

Distributed under the terms of the [BSD-3] license,
`openhcs-napari-roi-manager` is free and open source software. The original
upstream attribution is retained in [LICENSE](LICENSE).

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[napari]: https://github.com/napari/napari
[Cookiecutter]: https://github.com/audreyr/cookiecutter
[@napari]: https://github.com/napari
[MIT]: http://opensource.org/licenses/MIT
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[GNU GPL v3.0]: http://www.gnu.org/licenses/gpl-3.0.txt
[GNU LGPL v3.0]: http://www.gnu.org/licenses/lgpl-3.0.txt
[Apache Software License 2.0]: http://www.apache.org/licenses/LICENSE-2.0
[Mozilla Public License 2.0]: https://www.mozilla.org/media/MPL/2.0/index.txt
[cookiecutter-napari-plugin]: https://github.com/napari/cookiecutter-napari-plugin

[file an issue]: https://github.com/OpenHCSDev/openhcs-napari-roi-manager/issues

[napari]: https://github.com/napari/napari
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/
