from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout, Field

class MyColFormHelper(FormHelper):
    form_tag = False
    disable_csrf = True

class FileShareForm(forms.Form):
    title = forms.CharField(max_length=50)
    shared_file = forms.FileField()

    def __init__(self, *args, **kwargs):
        super(FileShareForm, self).__init__(*args, **kwargs)
        self.helper = MyColFormHelper()
        self.helper.layout = Layout(
            Div(
                Div(Field('title', css_class="form-control"), css_class=''),
                Div(Field('shared_file', css_class="form-control"), css_class=''),

                css_class = 'col-md-5'))


