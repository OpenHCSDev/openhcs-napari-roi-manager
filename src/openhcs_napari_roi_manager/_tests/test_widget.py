from collections.abc import Callable
from pathlib import Path

import napari
import numpy as np
from napari.layers import Shapes
from numpy.testing import assert_allclose
from roifile import roiread

from openhcs_napari_roi_manager import QRoiManager

_TEST_PATH = Path(__file__).parent


def _rectangle(y, x, size: float = 2):
    return np.array([[y, x], [y + size, x], [y + size, x + size], [y, x + size]])


def _nd_rectangle(*leading: float, y: float = 0, x: float = 0):
    rectangle = _rectangle(y, x)
    prefix = np.broadcast_to(leading, (len(rectangle), len(leading)))
    return np.concatenate([prefix, rectangle], axis=1)


def test_construction_without_shapes_adds_no_layer(
    make_napari_viewer: Callable[[], napari.Viewer],
):
    viewer = make_napari_viewer()
    image = viewer.add_image(np.zeros((8, 8)), name="image")
    before = list(viewer.layers)

    roi_manager = QRoiManager(viewer)

    assert list(viewer.layers) == before
    assert viewer.layers[0] is image
    assert roi_manager._layer is None
    assert roi_manager._roilist.rowCount() == 0


def test_construction_binds_active_native_shapes_without_copying(
    make_napari_viewer: Callable[[], napari.Viewer],
):
    viewer = make_napari_viewer()
    layer = viewer.add_shapes(
        [_rectangle(0, 0), _rectangle(5, 5)],
        shape_type=["rectangle", "ellipse"],
        features={"name": ["cell-1", "cell-2"], "area": [4.0, 4.0]},
        name="Cells",
    )
    before = list(viewer.layers)

    roi_manager = QRoiManager(viewer)

    assert list(viewer.layers) == before
    assert roi_manager._layer is layer
    assert type(layer) is Shapes
    assert roi_manager._roilist.rowCount() == 2
    assert roi_manager._roilist.get_column("name") == ["cell-1", "cell-2"]
    assert roi_manager._roilist.get_column("type") == ["rectangle", "ellipse"]


def test_connect_layer_is_public_native_owner_seam(
    make_napari_viewer: Callable[[], napari.Viewer],
):
    viewer = make_napari_viewer()
    manager = QRoiManager(viewer)
    layer = viewer.add_shapes(
        [_rectangle(0, 0)],
        shape_type="polygon",
        features={"name": ["native"]},
        name="Native",
    )

    manager.connect_layer(layer)

    assert manager._layer is layer
    assert manager._roilist.get_column("name") == ["native"]


def test_real_npe2_dock_binds_proxy_injected_viewer_without_copying(
    make_napari_viewer: Callable[[], napari.Viewer], qtbot
):
    viewer = make_napari_viewer()
    layer = viewer.add_shapes(
        [_rectangle(0, 0)],
        shape_type="rectangle",
        features={"name": ["proxied"]},
        name="Native",
    )
    before = list(viewer.layers)

    dock, widget = viewer.window.add_plugin_dock_widget(
        "openhcs-napari-roi-manager", "OpenHCS ROI Manager"
    )

    assert dock is not None
    assert isinstance(widget, QRoiManager)
    assert list(viewer.layers) == before
    assert widget._layer is layer
    assert widget._roilist.get_column("name") == ["proxied"]

    viewer.window.show()
    dock.show()
    qtbot.wait(1)
    dock.close()
    qtbot.wait(1)
    second = viewer.add_shapes(
        [_rectangle(5, 5)], features={"name": ["after-close"]}, name="Second"
    )
    assert widget._layer is None
    dock.show()
    qtbot.wait(1)
    assert widget._layer is second
    assert widget._roilist.get_column("name") == ["after-close"]


def test_selection_and_rename_are_bidirectional_native_state(
    make_napari_viewer: Callable[[], napari.Viewer],
):
    viewer = make_napari_viewer()
    layer = viewer.add_shapes(
        [_rectangle(0, 0), _rectangle(5, 5)],
        shape_type="rectangle",
        features={"name": ["first", "second"]},
    )
    manager = QRoiManager(viewer)

    manager._roilist.selectRow(1)
    assert layer.selected_data == {1}

    layer.selected_data = {0}
    layer.events.highlight()
    assert {index.row() for index in manager._roilist.selectedIndexes()} == {0}

    manager._roilist.item(0, 0).setText("renamed")
    assert layer.features["name"].tolist() == ["renamed", "second"]


def test_external_selection_scrolls_first_selected_row_into_view(
    make_napari_viewer: Callable[[], napari.Viewer], qtbot
):
    viewer = make_napari_viewer()
    layer = viewer.add_shapes(
        [_rectangle(index * 3, index * 3) for index in range(20)],
        shape_type="rectangle",
        features={"name": [f"roi-{index}" for index in range(20)]},
    )
    manager = QRoiManager(viewer)
    qtbot.addWidget(manager)
    table = manager._roilist
    table.setFixedHeight(120)
    manager.show()
    qtbot.wait(1)

    assert table.verticalScrollBar().maximum() > 0
    table.verticalScrollBar().setValue(table.verticalScrollBar().maximum())
    first_index = table.model().index(0, 0)
    assert not table.visualRect(first_index).intersects(table.viewport().rect())

    layer.selected_data = {0}
    layer.events.highlight()
    qtbot.wait(1)

    assert table.visualRect(first_index).intersects(table.viewport().rect())


def test_roi_table_expands_into_available_manager_space(
    make_napari_viewer: Callable[[], napari.Viewer], qtbot
):
    viewer = make_napari_viewer()
    viewer.add_shapes(
        [_rectangle(index * 3, index * 3) for index in range(20)],
        shape_type="rectangle",
        features={"name": [f"roi-{index}" for index in range(20)]},
    )
    manager = QRoiManager(viewer)
    qtbot.addWidget(manager)
    manager.resize(640, 520)
    manager.show()
    qtbot.wait(1)

    table = manager._roilist
    header = table.horizontalHeader()
    assert table.height() > 400
    assert table.width() > 400
    assert manager._btns.width() == 115
    assert header.sectionResizeMode(0) == header.ResizeMode.Stretch
    assert header.sectionResizeMode(1) == header.ResizeMode.ResizeToContents


def test_follows_active_shapes_identity_through_switch_reorder_and_remove(
    make_napari_viewer: Callable[[], napari.Viewer],
):
    viewer = make_napari_viewer()
    first = viewer.add_shapes(
        [_rectangle(0, 0)], features={"name": ["first"]}, name="First"
    )
    second = viewer.add_shapes(
        [_rectangle(5, 5)], features={"name": ["second"]}, name="Second"
    )
    image = viewer.add_image(np.zeros((8, 8)), name="Image")
    manager = QRoiManager(viewer)
    assert manager._layer is None

    viewer.layers.selection.active = first
    assert manager._layer is first
    assert manager._roilist.get_column("name") == ["first"]

    viewer.layers.move(viewer.layers.index(first), len(viewer.layers) - 1)
    assert manager._layer is first

    viewer.layers.selection.active = second
    assert manager._layer is second
    viewer.layers.selection.active = image
    assert manager._layer is None

    viewer.layers.selection.active = first
    viewer.layers.remove(first)
    assert manager._layer is not first


def test_native_data_and_feature_events_refresh_rows(
    make_napari_viewer: Callable[[], napari.Viewer],
):
    viewer = make_napari_viewer()
    layer = viewer.add_shapes(
        [_rectangle(0, 0)], features={"name": ["first"]}, name="ROIs"
    )
    manager = QRoiManager(viewer)

    layer.add(_rectangle(5, 5), shape_type="ellipse")
    assert manager._roilist.rowCount() == 2
    assert manager._roilist.get_column("type") == ["rectangle", "ellipse"]

    features = layer.features.copy()
    features["name"] = ["one", "two"]
    layer.features = features
    assert manager._roilist.get_column("name") == ["one", "two"]

    layer.selected_data = {0}
    manager._btns._remove_roi_btn.click()
    assert len(layer.data) == 1
    assert manager._roilist.rowCount() == 1
    assert manager._roilist.get_column("name") == ["two"]


def test_register_and_show_all_operate_on_bound_layer(
    make_napari_viewer: Callable[[], napari.Viewer],
):
    viewer = make_napari_viewer()
    layer = viewer.add_shapes(
        name="ROIs",
        ndim=2,
        edge_color="magenta",
        face_color=[0.2, 0.3, 0.4, 0.5],
        opacity=0.65,
    )
    manager = QRoiManager(viewer)

    manager.register(_rectangle(0, 0), shape_type="rectangle")
    manager.register(_rectangle(5, 5), shape_type="ellipse")
    assert len(layer.data) == 2
    assert manager._roilist.rowCount() == 2

    manager.select(1)
    original_edge_color = np.array(layer.edge_color, copy=True)
    original_face_color = np.array(layer.face_color, copy=True)
    manager.set_show_all(False)
    assert not manager._btns._show_all_checkbox.isChecked()
    assert_allclose(layer.edge_color[:, -1], 0)
    assert_allclose(layer.face_color[:, -1], 0)
    assert layer.opacity == 0.65
    assert layer.selected_data == {1}
    manager.register(_rectangle(8, 8), shape_type="rectangle")
    assert_allclose(layer.edge_color[:, -1], 0)
    assert_allclose(layer.face_color[:, -1], 0)
    manager.set_show_all(True)
    assert manager._btns._show_all_checkbox.isChecked()
    assert_allclose(layer.edge_color[:2], original_edge_color)
    assert_allclose(layer.face_color[:2], original_face_color)
    assert layer.edge_color[2, -1] > 0
    assert layer.opacity == 0.65


def test_show_all_style_restores_on_layer_switch_and_close(
    make_napari_viewer: Callable[[], napari.Viewer],
):
    viewer = make_napari_viewer()
    first = viewer.add_shapes(
        [_rectangle(0, 0)], edge_color="red", face_color="blue", opacity=0.4
    )
    second = viewer.add_shapes(
        [_rectangle(5, 5)], edge_color="green", face_color="yellow", opacity=0.8
    )
    viewer.layers.selection.active = first
    manager = QRoiManager(viewer)
    first_edge = np.array(first.edge_color, copy=True)
    first_face = np.array(first.face_color, copy=True)
    second_edge = np.array(second.edge_color, copy=True)
    second_face = np.array(second.face_color, copy=True)

    manager.set_show_all(False)
    viewer.layers.selection.active = second

    assert_allclose(first.edge_color, first_edge)
    assert_allclose(first.face_color, first_face)
    assert first.opacity == 0.4
    assert_allclose(second.edge_color[:, -1], 0)
    assert_allclose(second.face_color[:, -1], 0)
    assert second.opacity == 0.8

    manager.close()
    assert_allclose(second.edge_color, second_edge)
    assert_allclose(second.face_color, second_face)
    assert second.opacity == 0.8


def test_show_all_tracks_external_recolor_and_removal_on_native_owner(
    make_napari_viewer: Callable[[], napari.Viewer],
):
    viewer = make_napari_viewer()
    layer = viewer.add_shapes(
        [_rectangle(0, 0), _rectangle(5, 5), _rectangle(10, 10)],
        edge_color=["red", "green", "blue"],
        face_color=["blue", "red", "green"],
        opacity=0.55,
    )
    manager = QRoiManager(viewer)
    manager.set_show_all(False)

    layer.edge_color = "cyan"
    layer.face_color = "magenta"
    assert_allclose(layer.edge_color[:, -1], 0)
    assert_allclose(layer.face_color[:, -1], 0)

    layer.selected_data = {1}
    layer.remove_selected()
    assert len(layer.data) == 2
    assert manager._roilist.rowCount() == 2
    assert_allclose(layer.edge_color[:, -1], 0)
    assert_allclose(layer.face_color[:, -1], 0)

    manager.set_show_all(True)
    assert_allclose(layer.edge_color, np.array([[0, 1, 1, 1]] * 2))
    assert_allclose(layer.face_color, np.array([[1, 0, 1, 1]] * 2))
    assert layer.opacity == 0.55


def test_close_disconnects_active_layer_and_reopen_rebinds_once(
    make_napari_viewer: Callable[[], napari.Viewer], qtbot
):
    viewer = make_napari_viewer()
    first = viewer.add_shapes(
        [_rectangle(0, 0)], edge_color="red", face_color="blue", name="First"
    )
    second = viewer.add_shapes(
        [_rectangle(5, 5)], edge_color="green", face_color="yellow", name="Second"
    )
    viewer.layers.selection.active = first
    manager = QRoiManager(viewer)
    qtbot.addWidget(manager)
    original_layers = tuple(viewer.layers)
    first_edge = np.array(first.edge_color, copy=True)
    second_edge = np.array(second.edge_color, copy=True)

    manager.set_show_all(False)
    manager.close()
    assert manager._layer is None
    assert_allclose(first.edge_color, first_edge)

    viewer.layers.selection.active = second
    assert manager._layer is None
    assert_allclose(second.edge_color, second_edge)

    manager.set_show_all(True)
    manager.show()
    qtbot.wait(1)
    assert manager._layer is second
    assert tuple(viewer.layers) == original_layers

    manager.close()
    manager.show()
    qtbot.wait(1)
    second.add(_rectangle(10, 10))
    assert manager._layer is second
    assert manager._roilist.rowCount() == 2
    assert tuple(viewer.layers) == original_layers


def test_new_set_is_explicit_and_preserves_viewer_ndim(
    make_napari_viewer: Callable[[], napari.Viewer],
):
    viewer = make_napari_viewer()
    viewer.add_image(np.zeros((2, 3, 8, 8)), name="image")
    manager = QRoiManager(viewer)
    before = len(viewer.layers)

    layer = manager.new_layer()

    assert len(viewer.layers) == before + 1
    assert manager._layer is layer
    assert type(layer) is Shapes
    assert layer.ndim == 4
    assert len(layer.data) == 0


def test_json_roundtrip_preserves_nd_geometry_and_roi_names(
    make_napari_viewer: Callable[[], napari.Viewer], tmp_path: Path
):
    viewer = make_napari_viewer()
    data = [_nd_rectangle(2, 3, y=1, x=1), _nd_rectangle(4, 5, y=6, x=6)]
    layer = viewer.add_shapes(
        data,
        shape_type=["rectangle", "ellipse"],
        features={"name": ["one", "two"], "length": [1.5, 2.5]},
        name="ROIs",
    )
    manager = QRoiManager(viewer)
    path = tmp_path / "rois.json"

    manager.save_roiset(path=path)
    original_identity = manager._layer
    manager.load_roiset(path=path, append=False)

    assert manager._layer is original_identity is layer
    assert layer.ndim == 4
    assert_allclose(layer.data[0], data[0])
    assert_allclose(layer.data[1], data[1])
    assert layer.shape_type == ["rectangle", "ellipse"]
    assert layer.features["name"].tolist() == ["one", "two"]
    assert layer.features["length"].tolist() == [1.5, 2.5]


def test_imagej_roundtrip_preserves_nd_positions(
    make_napari_viewer: Callable[[], napari.Viewer], tmp_path: Path
):
    viewer = make_napari_viewer()
    data = [_nd_rectangle(4, 5, y=1, x=2)]
    layer = viewer.add_shapes(
        data,
        shape_type="rectangle",
        features={"name": ["nd-roi"]},
        name="ROIs",
    )
    manager = QRoiManager(viewer)
    path = tmp_path / "rois.zip"

    manager.save_roiset(path=path)
    roi = roiread(path)[0]
    assert roi.t_position == 5
    assert roi.z_position == 6

    manager.load_roiset(path=path, append=False)
    assert layer.ndim == 4
    assert_allclose(layer.data[0][:, :2], np.array([[4, 5]] * 4))


def test_existing_imagej_fixture_still_roundtrips(
    make_napari_viewer: Callable[[], napari.Viewer], tmp_path: Path
):
    viewer = make_napari_viewer()
    layer = viewer.add_shapes(name="ROIs", ndim=2)
    manager = QRoiManager(viewer)
    manager.load_roiset(path=_TEST_PATH / "test-rois.zip", append=True)
    data0 = [np.array(shape, copy=True) for shape in layer.data]
    path = tmp_path / "test_save_roiset.zip"

    manager.save_roiset(path=path)
    manager.load_roiset(path=path, append=False)

    assert len(data0) == len(layer.data)
    for before, after in zip(data0, layer.data, strict=True):
        assert_allclose(before, after, rtol=1e-5, atol=1e-8)
