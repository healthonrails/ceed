import trio
import math

from .examples.stages import create_test_stages, make_stage, StageWrapper, \
    stage_classes, assert_stages_same
from typing import Type, List, Union
from ceed.tests.ceed_app import CeedTestApp
from ceed.tests.test_app import replace_text, touch_widget, escape
from ceed.stage import CeedStage, CeedStageRef
from ceed.function import CeedFuncRef, FuncBase, FuncGroup
from ceed.shape import CeedShape, CeedShapeGroup
from .examples.shapes import assert_add_three_groups
from .examples.funcs import create_funcs, GroupFunction
from .test_func import assert_func_params_in_gui, \
    replace_last_ref_with_original_func, assert_funcs_same


async def assert_set_params_in_gui(
        stage_app: CeedTestApp, stage: StageWrapper, settings=None,
        check_name=False):
    opened_settings = settings is None
    if opened_settings:
        settings = await open_stage_settings(stage_app, stage.stage)

    if check_name:
        name = stage_app.resolve_widget(settings).down(
            test_name='stage name')()
        assert name.text != stage.name
        assert name.text == stage.stage.name
        await replace_text(stage_app, name, stage.name)
        assert name.text == stage.name
        assert name.text == stage.stage.name

    # verify colors
    for color in ('r', 'g', 'b'):
        widget = stage_app.resolve_widget(settings).down(
            test_name='stage color {}'.format(color))()
        prop = 'color_{}'.format(color)
        # the stage values should always match the GUI values
        assert getattr(stage.stage, prop) == (widget.state == 'down')
        # if the wrapper need to change the value, do it
        if getattr(stage, prop) != getattr(stage.stage, prop):
            await touch_widget(stage_app, widget)

        # make sure it was changed
        assert getattr(stage.stage, prop) == (widget.state == 'down')
        assert getattr(stage, prop) == getattr(stage.stage, prop)

    # parallel vs serial
    serial = stage_app.resolve_widget(settings).down(
        test_name='stage serial')()
    parallel = stage_app.resolve_widget(settings).down(
        test_name='stage parallel')()
    assert (stage.stage.order == 'serial') == (serial.state == 'down') and \
        (stage.stage.order == 'parallel') == (parallel.state == 'down')

    # set the GUI to the correct value
    if stage.order == 'parallel' and parallel.state != 'down':
        await touch_widget(stage_app, parallel)
    elif stage.order == 'serial' and serial.state != 'down':
        await touch_widget(stage_app, serial)
    assert (stage.stage.order == 'serial') == (serial.state == 'down') and \
        (stage.stage.order == 'parallel') == (parallel.state == 'down')
    assert (stage.order == 'serial') == (serial.state == 'down') and \
        (stage.order == 'parallel') == (parallel.state == 'down')

    # complete_on all vs any
    all_w = stage_app.resolve_widget(settings).down(
        test_name='stage finish all')()
    any_w = stage_app.resolve_widget(settings).down(
        test_name='stage finish any')()
    assert (stage.stage.complete_on == 'all') == (all_w.state == 'down') and \
        (stage.stage.complete_on == 'any') == (any_w.state == 'down')

    # set the GUI to the correct value
    if stage.complete_on == 'all' and all_w.state != 'down':
        await touch_widget(stage_app, all_w)
    elif stage.complete_on == 'any' and any_w.state != 'down':
        await touch_widget(stage_app, any_w)

    assert (stage.stage.complete_on == 'all') == (all_w.state == 'down') and \
        (stage.stage.complete_on == 'any') == (any_w.state == 'down')
    assert (stage.complete_on == 'all') == (all_w.state == 'down') and \
        (stage.complete_on == 'any') == (any_w.state == 'down')

    if opened_settings:
        await escape(stage_app)
    return settings


async def assert_stage_params_in_gui(
        stage_app: CeedTestApp, stage: StageWrapper, settings=None,
        check_name=False):
    opened_settings = settings is None
    if opened_settings:
        settings = await open_stage_settings(stage_app, stage.stage)

    if check_name:
        name = stage_app.resolve_widget(settings).down(
            test_name='stage name')()
        name_label = stage_app.resolve_widget(stage.stage.display).down(
            test_name='stage label')()
        assert name.text == stage.name
        assert name_label.text == stage.name
        assert name.text == stage.stage.name

    # verify colors
    for color in ('r', 'g', 'b'):
        widget = stage_app.resolve_widget(settings).down(
            test_name='stage color {}'.format(color))()
        prop = 'color_{}'.format(color)
        assert getattr(stage.stage, prop) == (widget.state == 'down')
        assert getattr(stage, prop) == getattr(stage.stage, prop)

    # parallel vs serial
    serial = stage_app.resolve_widget(settings).down(
        test_name='stage serial')()
    parallel = stage_app.resolve_widget(settings).down(
        test_name='stage parallel')()
    assert (stage.stage.order == 'serial') == (serial.state == 'down') and \
        (stage.stage.order == 'parallel') == (parallel.state == 'down')

    # complete_on all vs any
    all_w = stage_app.resolve_widget(settings).down(
        test_name='stage finish all')()
    any_w = stage_app.resolve_widget(settings).down(
        test_name='stage finish any')()
    assert (stage.stage.complete_on == 'all') == (all_w.state == 'down') and \
        (stage.stage.complete_on == 'any') == (any_w.state == 'down')

    if opened_settings:
        await escape(stage_app)
    return settings


async def replace_last_ref_with_original_stage(
        stage_app: CeedTestApp,
        stages: List[Union[CeedStageRef, CeedStage]], name: str):
    start_stages = stages[:]
    ref_stage = stages[-1]
    # it should be a ref to start with
    assert isinstance(ref_stage, CeedStageRef)
    # make sure the class name matches - we added the right class
    assert ref_stage.stage.name == name

    # the label of the new sub-stage
    sub_stage_widget = ref_stage.display
    name_w = stage_app.resolve_widget(sub_stage_widget).down(
        test_name='stage label')()
    assert name_w.text == name
    # replace the ref with a copy of the stage
    ref_btn = stage_app.resolve_widget(sub_stage_widget).down(
        test_name='stage settings open')()
    await touch_widget(stage_app, ref_btn)

    # should now have replaced the ref with a copy of the original
    assert ref_stage not in stages
    assert len(stages) == len(start_stages)

    new_stage = stages[-1]
    assert ref_stage is not new_stage
    assert stages[:-1] == start_stages[:-1]
    # it should not be a ref anymore
    assert not isinstance(new_stage, CeedStageRef)

    assert_stages_same(ref_stage.stage, new_stage)

    return new_stage


async def open_stage_settings(app: CeedTestApp, stage: CeedStage):
    settings_btn = app.resolve_widget(stage.display).down(
        test_name='stage settings open')()
    await touch_widget(app, settings_btn)

    return app.resolve_widget().down(test_name='stage settings')()


async def test_stage_find_shape_in_all_stages(stage_app: CeedTestApp):
    (s1, s2, s3), (group, shape1, shape2, shape3) = create_test_stages(
        stage_app=stage_app, show_in_gui=True)
    await stage_app.wait_clock_frames(2)

    for shape in (shape1, shape2, shape3):
        for stage in (s1, s2, s3):
            assert shape.shape in [s.shape for s in stage.stage.shapes]
        assert shape.shape in group.shapes

    stage_app.shape_factory.remove_shape(shape2.shape)
    await stage_app.wait_clock_frames(2)

    for shape in (shape1, shape3):
        for stage in (s1, s2, s3):
            assert shape.shape in [s.shape for s in stage.stage.shapes]
        assert shape.shape in group.shapes
    for shape in (shape2, ):
        for stage in (s1, s2, s3):
            assert shape.shape not in [s.shape for s in stage.stage.shapes]
        assert shape.shape not in group.shapes

    stage_app.shape_factory.remove_shape(shape1.shape)
    await stage_app.wait_clock_frames(2)

    for shape in (shape3, ):
        for stage in (s1, s2, s3):
            assert shape.shape in [s.shape for s in stage.stage.shapes]
        assert shape.shape in group.shapes
    for shape in (shape2, shape1):
        for stage in (s1, s2, s3):
            assert shape.shape not in [s.shape for s in stage.stage.shapes]
        assert shape.shape not in group.shapes

    stage_app.shape_factory.remove_shape(shape3.shape)
    await stage_app.wait_clock_frames(2)

    for shape in (shape2, shape1, shape3):
        for stage in (s1, s2, s3):
            assert shape.shape not in [s.shape for s in stage.stage.shapes]
        assert shape.shape not in group.shapes


async def test_add_empty_stage(stage_app: CeedTestApp):
    stage_factory = stage_app.stage_factory
    assert not stage_factory.stages
    assert not stage_factory.stage_names

    # add first empty stage
    add_stage = stage_app.resolve_widget().down(test_name='add empty stage')()
    await touch_widget(stage_app, add_stage)

    assert stage_factory.stages
    stage = stage_factory.stages[0]
    assert list(stage_factory.stage_names.values()) == [stage]
    assert stage.display.show_more

    # select the stage and add stage to it
    name_label = stage_app.resolve_widget(stage.display).down(
        test_name='stage label')()
    assert not stage.display.selected

    await touch_widget(stage_app, name_label)
    assert stage.display.selected
    await touch_widget(stage_app, add_stage)
    assert stage_factory.stages == [stage]

    # deselect the stage and add stage globally
    assert stage.display.selected
    await touch_widget(stage_app, name_label)
    await touch_widget(stage_app, add_stage)

    assert len(stage_factory.stages) == 2
    assert stage_factory.stages[0] is stage


async def test_gui_add_stages(stage_app: CeedTestApp):
    stages = []
    add_stage = stage_app.resolve_widget().down(test_name='add empty stage')()
    for i, stage_cls in enumerate(stage_classes):
        stage = stage_cls(app=stage_app, show_in_gui=False)
        stages.append(stage)

        # don't keep more than two stages so the list is not too long
        if i >= 2:
            oldest_stage = stages.pop(0)
            assert oldest_stage.stage in stage_app.stage_factory.stages
            remove_btn = stage_app.resolve_widget(
                oldest_stage.stage.display).down(test_name='del btn stage')()
            await touch_widget(stage_app, remove_btn)
            assert oldest_stage.stage not in stage_app.stage_factory.stages

        # add the stage
        await touch_widget(stage_app, add_stage)
        assert len(stage_app.stage_factory.stages) == min(2, i + 1)
        stage.stage = stage_app.stage_factory.stages[-1]

        # show the settings for the stage
        widget = stage.stage.display
        settings = await open_stage_settings(stage_app, stage.stage)

        # check default name
        name = stage_app.resolve_widget(settings).down(
            test_name='stage name')()
        assert not name.disabled, "root stages can be renamed"
        name_label = stage_app.resolve_widget(widget).down(
            test_name='stage label')()
        original_name = name.text
        assert stage.name != original_name
        assert original_name == name_label.text
        assert original_name in stage_app.stage_factory.stage_names
        assert stage.name not in stage_app.stage_factory.stage_names

        # change the stage name
        await replace_text(stage_app, name, stage.name)
        assert name.text == stage.name
        assert name_label.text == stage.name
        assert original_name not in stage_app.stage_factory.stage_names
        assert stage.name in stage_app.stage_factory.stage_names

        await assert_set_params_in_gui(stage_app, stage, settings)

        # close the settings widget
        await escape(stage_app)


async def test_gui_add_sub_stages(stage_app: CeedTestApp):
    add_stage = stage_app.resolve_widget().down(test_name='add empty stage')()
    await touch_widget(stage_app, add_stage)

    base_stage: CeedStage = stage_app.stage_factory.stages[0]
    name_label = stage_app.resolve_widget(base_stage.display).down(
        test_name='stage label')()
    await touch_widget(stage_app, name_label)
    assert base_stage.display.selected
    assert not base_stage.stages

    stages = []
    for i, stage_cls in enumerate(stage_classes[:4]):
        stage = stage_cls(app=stage_app, show_in_gui=False)
        stages.append(stage)

        # don't keep more than two stages so the list is not too long
        if i >= 2:
            oldest_stage = stages.pop(0)
            assert oldest_stage.stage in base_stage.stages
            remove_btn = stage_app.resolve_widget(
                oldest_stage.stage.display).down(test_name='del btn stage')()
            await touch_widget(stage_app, remove_btn)
            assert oldest_stage.stage not in base_stage.stages

        if not base_stage.display.selected:
            await touch_widget(stage_app, name_label)
            assert base_stage.display.selected

        # add the stage
        await touch_widget(stage_app, add_stage)
        assert len(base_stage.stages) == min(2, i + 1)
        stage.stage = base_stage.stages[-1]

        await assert_set_params_in_gui(stage_app, stage, check_name=False)


async def test_gui_drag_shape_to_stage(stage_app: CeedTestApp):
    (group, group2, group3), (shape1, shape2, shape3) = \
        assert_add_three_groups(
            shape_factory=stage_app.shape_factory, app=stage_app,
            show_in_gui=True)
    await stage_app.wait_clock_frames(2)

    (s1, s2, s3), _ = create_test_stages(
        stage_app=stage_app, add_func=False, add_shapes=False)
    await stage_app.wait_clock_frames(2)

    # multiple stages
    for stage in (s2, s3):
        container = stage.stage.display.shape_widget
        shapes = stage.stage.shapes
        assert not shapes

        # drag each shape to the stage
        added_shapes = []
        for i, shape in enumerate((shape1, group2, shape3, shape2)):
            if isinstance(shape, CeedShapeGroup):
                src = stage_app.resolve_widget(shape.widget).down(
                    test_name='group drag button')()
            else:
                shape = shape.shape
                src = stage_app.resolve_widget(shape.widget).down(
                    test_name='shape drag')()

            async for _ in stage_app.do_touch_drag_follow(
                    widget=src, target_widget=container,
                    target_widget_loc=('center_x', 'y'), drag_n=15):
                pass

            # check that shape was added
            assert len(shapes) == min(3, i + 1)
            assert shape is shapes[-1].shape

            # make sure label matches
            name_label = stage_app.resolve_widget(shapes[-1].display).down(
                test_name='stage shape name')()
            assert name_label.text == shape.name

            added_shapes.append(shapes[-1])

            # don't keep more than two stages so the list is not too long
            if i >= 2:
                oldest_shape = added_shapes.pop(0)
                assert oldest_shape in shapes
                remove_btn = stage_app.resolve_widget(
                    oldest_shape.display).down(
                    test_name='stage shape del')()
                await touch_widget(stage_app, remove_btn)
                assert oldest_shape not in shapes
            await stage_app.wait_clock_frames(2)


async def test_gui_drag_func_to_stage(stage_app: CeedTestApp):
    global_funcs = create_funcs(func_app=stage_app, show_in_gui=True)
    group_func: GroupFunction = global_funcs[-1]
    ff1 = group_func.wrapper_funcs[0]
    ff2 = group_func.wrapper_funcs[1]
    global_funcs = [
        (ff1, True)] + [(f, False) for f in global_funcs] + [(ff2, True)]
    await stage_app.wait_clock_frames(2)

    (s1, s2, s3), _ = create_test_stages(
        stage_app=stage_app, add_func=False, add_shapes=False)
    await stage_app.wait_clock_frames(2)

    # multiple funcs
    for stage in (s2, s3):
        container = stage.stage.display.func_widget
        functions = stage.stage.functions
        assert not functions

        # drag each func to the stage
        added_funcs = []
        for i, (func, is_sub_func) in enumerate(global_funcs):
            src = stage_app.resolve_widget(func.func.display).down(
                test_name='func drag btn')()

            async for _ in stage_app.do_touch_drag_follow(
                    widget=src, target_widget=container,
                    target_widget_loc=('center_x', 'y'),
                    target_widget_offset=(0, 5)):
                pass

            # check that shape was added
            assert len(functions) == min(3, i + 1)
            assert functions[-1] is not func.func
            if is_sub_func:
                assert isinstance(functions[-1], (FuncBase, FuncGroup))
                assert_funcs_same(functions[-1], func.func)
            else:
                assert isinstance(functions[-1], CeedFuncRef)
                assert func.func is functions[-1].func
                await replace_last_ref_with_original_func(
                    stage_app, functions, func.func.name)

            added_funcs.append(functions[-1])

            # don't keep more than two funcs so the list is not too long
            if i >= 2:
                oldest_func = added_funcs.pop(0)
                assert oldest_func in functions
                remove_btn = stage_app.resolve_widget(
                    oldest_func.display).down(
                    test_name='del_btn_func')()
                await touch_widget(stage_app, remove_btn)
                assert oldest_func not in functions

            await stage_app.wait_clock_frames(2)


async def test_gui_drag_stage_to_stage(stage_app: CeedTestApp):
    (s1, s2, s21), _ = create_test_stages(
        stage_app=stage_app, show_in_gui=True, add_func=False,
        add_shapes=False)
    (s3, s4, s41), _ = create_test_stages(
        stage_app=stage_app, show_in_gui=True, add_func=False,
        add_shapes=False)
    await stage_app.wait_clock_frames(2)

    # collapse stages to not take up space
    for stage in (s1, s21, s3):
        stage.stage.display.show_more = False
    await stage_app.wait_clock_frames(2)

    # multiple funcs
    for stage in (s4, s41):
        container = stage.stage.display.stage_widget
        stages = stage.stage.stages
        n_start = 0 if stage is s41 else 1
        assert len(stages) == n_start

        # drag each func to the stage
        added_stages = []
        for i, src_stage in enumerate((s1, s2, s21, s3)):
            src = stage_app.resolve_widget(src_stage.stage.display).down(
                test_name='stage drag btn')()

            async for _ in stage_app.do_touch_drag_follow(
                    widget=src, target_widget=container,
                    target_widget_loc=('center_x', 'y'),
                    target_widget_offset=(0, 5)):
                pass

            # check that shape was added
            assert len(stages) == min(3, i + 1) + n_start

            assert stages[-1] is not src_stage.stage
            if src_stage is s21:
                assert isinstance(stages[-1], CeedStage)
                assert_stages_same(stages[-1], src_stage.stage)
            else:
                assert isinstance(stages[-1], CeedStageRef)
                assert src_stage.stage is stages[-1].stage
                await replace_last_ref_with_original_stage(
                    stage_app, stages, src_stage.stage.name)

            added_stages.append(stages[-1])

            # don't keep more than two stages so the list is not too long
            if i >= 2:
                oldest_stage = added_stages.pop(0)
                assert oldest_stage in stages
                remove_btn = stage_app.resolve_widget(
                    oldest_stage.display).down(
                    test_name='del btn stage')()
                await touch_widget(stage_app, remove_btn)
                assert oldest_stage not in stages

            await stage_app.wait_clock_frames(2)


async def test_recursive_play_stage_intensity(stage_app: CeedTestApp):
    from ..test_stages import create_recursive_stages
    from .examples.shapes import CircleShapeP1, CircleShapeP2
    from kivy.clock import Clock
    root, g1, g2, s1, s2, s3, s4, s5, s6 = create_recursive_stages(
        stage_app.stage_factory, app=stage_app)

    from ceed.function.plugin import LinearFunc
    for i, stage in enumerate((s1, s2, s3, s4, s5, s6)):
        stage.stage.add_func(LinearFunc(
            function_factory=stage_app.function_factory, b=0, m=.1,
            duration=(i % 2 + 1) * 5))

    shape = CircleShapeP1(
        app=None, painter=stage_app.shape_factory, show_in_gui=True)

    shape2 = CircleShapeP2(
        app=None, painter=stage_app.shape_factory, show_in_gui=True)
    s1.stage.add_shape(shape.shape)
    s4.stage.add_shape(shape.shape)
    s5.stage.add_shape(shape.shape)
    s2.stage.add_shape(shape2.shape)
    s3.stage.add_shape(shape2.shape)
    s6.stage.add_shape(shape2.shape)

    root.show_in_gui()
    await stage_app.wait_clock_frames(2)

    frame = 0
    event = None
    trio_event = trio.Event()
    rate = stage_app.view_controller.frame_rate = 10
    num_frames = rate * (10 + 5 + 10 + 5)
    initial_frames = Clock.frames_displayed
    stage_app.view_controller.use_software_frame_rate = False
    stage_app.view_controller.flip_projector = False

    def verify_intensity(*largs):
        nonlocal frame
        if Clock.frames_displayed <= initial_frames + 1:
            return

        if not stage_app.view_controller.stage_active:
            event.cancel()
            trio_event.set()
            assert frame == num_frames
            return

        points = stage_app.get_widget_pos_pixel(
            stage_app.shape_factory, [shape.center, shape2.center])
        points = [[c / 255 for c in p] for p in points]
        (r1, g1, b1, _), (r2, g2, b2, _) = points

        for s, start, e in [(s1, 0, 5), (s4, 15, 25), (s5, 25, 30)]:
            if start * rate <= frame < e * rate:
                val = (frame - start * rate) / rate * .1
                assert math.isclose(r1, val, abs_tol=2 / 255) \
                    if s.color_r else r1 == 0
                assert math.isclose(g1, val, abs_tol=2 / 255) \
                    if s.color_g else g1 == 0
                assert math.isclose(b1, val, abs_tol=2 / 255) \
                    if s.color_b else b1 == 0
                break
        else:
            assert r1 == 0
            assert g1 == 0
            assert b1 == 0

        for s, start, e in [(s2, 0, 10), (s3, 10, 15), (s6, 25, 30)]:
            if start * rate <= frame < e * rate:
                val = (frame - start * rate) / rate * .1
                assert math.isclose(r2, val, abs_tol=2 / 255) \
                    if s.color_r else r2 == 0
                assert math.isclose(g2, val, abs_tol=2 / 255) \
                    if s.color_g else g2 == 0
                assert math.isclose(b2, val, abs_tol=2 / 255) \
                    if s.color_b else b2 == 0
                break
        else:
            assert r2 == 0
            assert g2 == 0
            assert b2 == 0

        frame += 1

    event = Clock.create_trigger(verify_intensity, timeout=0, interval=True)
    event()
    stage_app.view_controller.request_stage_start(root.name)

    await trio_event.wait()

    stage_app.view_controller.request_stage_end()
    event.cancel()
