import contextlib
from functools import partial

import solara
from solara.alias import rv
from pydantic import ValidationError, BaseModel


@solara.component
def ValidationForm(data: BaseModel, layout=None, field_options=None, global_options=None):
    field_options=field_options or {}
    global_options=global_options or {}

    reactive_value = solara.use_reactive(data)
    error_value = solara.use_reactive({k: [] for k in reactive_value.value.__fields__})

    def updater(name, value):
        print('updating', name, value)
        try:
            reactive_value.update(**{name: value})
            if error_value.value[name]:
                error_value.update(**{name: []})
        except ValidationError as e:
            errors = e.errors()
            if len(errors) > 1:
                raise ValueError("Can only handle one error") from e
            error = errors[0]
            error_value.update(**{name: [error['msg']]})

    layout = layout or solara.Column()
    with layout:
        for name, field in reactive_value.value.__fields__.items():
            upd_func = partial(updater, name)
            f_opt = field_options.get(name, {})

            if 'tooltip' in field_options:
                cm = solara.Tooltip(f_opt['tooltip'])
            else:
                cm = contextlib.nullcontext()

            kwargs = {k: v for k, v in f_opt.items() if k not in {'tooltip'}}

            label = field.field_info.title or name
            textfield_kwargs = dict(label=label, v_model=getattr(reactive_value.value, name), error_messages=error_value.value[name], on_v_model=upd_func, **kwargs, **global_options)

            if issubclass(field.type_, float):
                textfield_kwargs['type'] = "number"
                textfield_kwargs['attributes'] = {"step": "any"} # any?
            elif issubclass(field.type_, int):
                textfield_kwargs['type'] = "number"
                textfield_kwargs['attributes'] = {"step": 1}
            elif issubclass(field.type_, str):
                textfield_kwargs['type'] = "text"
            else:
                continue

            with cm:
                rv.TextField(**textfield_kwargs)

    solara.Button(label='print', on_click=lambda: print(reactive_value.value))

