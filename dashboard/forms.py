from django import forms

class SlideForm(forms.Form):
    slidename = forms.CharField(required=True)
    scanned_by = forms.CharField(required=False)
    scanned_date = forms.DateField(required=False)
    inserted_by = forms.CharField(required=False)
    inserted_date = forms.DateField(required=False)
    slide_type = forms.CharField(required=True)
    annotations = forms.BooleanField(required=False)
    slide_upload = forms.FileField(required=True)
    label_upload = forms.FileField(required=False)
    parent = forms.IntegerField(required=True)
