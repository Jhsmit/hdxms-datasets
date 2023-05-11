import contextlib
from functools import partial
from typing import Callable

import solara
from solara.alias import rv
from pydantic import ValidationError, BaseModel

@solara.component
def ValidationForm(value: BaseModel, on_value: Callable[[BaseModel], None] = None, layout=None, field_options=None, global_options=None):
    field_options = field_options or {}
    global_options = global_options or {}

    # value of the pydantic model
    model_value = solara.use_reactive(value, on_value)

    # value of the form, allows for illegal values
    form_value = solara.use_reactive(model_value.value.dict())

    # dictionary with error messages from validation
    error_value = solara.use_reactive({k: [] for k in model_value.value.__fields__})

    def updater(name, value):
        form_value.update(**{name: value})
        try:
            model_value.update(**{name: value})
            if error_value.value[name]:
                error_value.update(**{name: []})
        except ValidationError as e:
            errors = e.errors()
            if len(errors) > 1:
                raise ValueError("Can only handle one error") from e
            error = errors[0]
            error_value.update(**{name: [error['msg']]})

    layout_cm = layout or solara.Column
    with layout_cm():
        for name, field in model_value.value.__fields__.items():
            upd_func = partial(updater, name)
            f_opt = field_options.get(name, {})

            if tooltip := field.field_info.description:
                cm = solara.Tooltip(tooltip)
            else:
                cm = contextlib.nullcontext()

            kwargs = {k: v for k, v in f_opt.items() if k not in {'tooltip'}}

            label = field.field_info.title or humanize_snake_case(name)
            textfield_kwargs = dict(label=label, v_model=form_value.value[name], error_messages=error_value.value[name], on_v_model=upd_func, **field_options, **global_options)

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

    solara.Button(label='print', on_click=lambda: print(model_value.value))


def humanize_snake_case(s: str) -> str:
    # the human already thought about humanization or does not stick to snake_case
    if any(c.isupper() for c in s):
        return s
    else:
        return s.replace('_', ' ').title()