__author__ = 'ratna'
from django import forms
from django.utils.translation import ugettext as _, ugettext_lazy

APPROVE_CHOICES = (
    ('add', ugettext_lazy('Add Approval')),
    ('remove', ugettext_lazy('Remove Approval')),
)

APPROVER_TYPE_CHOICES = (
    ('approver', ugettext_lazy('Approver')),
    ('consent', ugettext_lazy('Consent')),
    ('notify', ugettext_lazy('Notify')),
)

APPROVAL_TYPE_CHOICES = (
    ('any', ugettext_lazy('Any One')),
    ('all', ugettext_lazy('All')),
)

class ApprovalForm(forms.Form):
    approver = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'id': 'autocompleted',
                'data-provide': 'typeahead',
                'autocomplete': 'off'
            })
    )
    approval_option = forms.ChoiceField(choices=APPROVE_CHOICES, widget=forms.Select())
    label_type = forms.IntegerField(widget=forms.TextInput(), required=True)
    approver_type = forms.ChoiceField(choices=APPROVER_TYPE_CHOICES, widget=forms.Select())
    approval_type = forms.ChoiceField(choices=APPROVAL_TYPE_CHOICES, widget=forms.Select())

    def __init__(self, username):
        self.username = username
        super(ApprovalForm, self).__init__()

