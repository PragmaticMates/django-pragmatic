from crispy_forms.helper import FormHelper


class SingleSubmitFormHelper(FormHelper):
    def __init__(self, form=None):
        super().__init__(form)
        self.attrs['onsubmit'] = "submit.disabled=true; return true;"
