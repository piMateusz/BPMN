from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.urls import reverse

from .forms import ModelFormWithFileField, ModelCsvHeaderForm
from .models import BpmnFile
from .bpmn_utils.graph import display_bpmn_model

import os

# Create your views here.


def myajaxtestview(request):
    node_threshold = int(request.POST['node_threshold'])
    edge_threshold = int(request.POST['edge_threshold'])
    file_name = request.POST['file_name']
    file_path = os.path.join(settings.MEDIA_ROOT, file_name)

    img_src, trace_max, color_max = display_bpmn_model(file_path, node_threshold, edge_threshold)

    return HttpResponse(img_src)


def bpmn_model_detail_view(request, pk):
    try:
        model_file = BpmnFile.objects.get(pk=pk)
    except BpmnFile.DoesNotExist:
        raise Http404("Bpmn model does not exist")

    file_path = model_file.file.path
    file_name = model_file.file.name

    img_src, trace_max, color_max = display_bpmn_model(file_path, node_threshold=0, edge_threshold=0)

    return render(request, 'bpmn_app/bpmn_model_detail.html',
                  {'file_name': file_name, 'img_src': img_src,
                   'trace_max': trace_max + 1, 'color_max': color_max + 1})


class BpmnModelListView(ListView):
    template_name = "bpmn_app/bpmn_home.html"
    context_object_name = "bpmn_files"
    model = BpmnFile


def upload_file(request):
    if request.method == 'POST':
        form = ModelFormWithFileField(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.save()
            # TODO correct this redirect
            # HttpResponseRedirect(reverse(contact_details, args=(new_contact.pk,)))
            return HttpResponseRedirect(reverse('bpmn-model-column-headers', kwargs={'pk': uploaded_file.pk}))
    else:
        form = ModelFormWithFileField()
    return render(request, 'bpmn_app/bpmn_upload.html', {'form': form})


def choose_excel_column_headers(request, pk):
    try:
        model_file = BpmnFile.objects.get(pk=pk)
    except BpmnFile.DoesNotExist:
        raise Http404("Bpmn model does not exist")

    file_path = model_file.file.path
    file_name = model_file.file.name

    # TODO match strings
    case_id_col_name = "Case ID"
    timestamp_col_name = "Start Timestamp"
    activity_col_name = "Activity"

    if request.method == 'POST':
        form = ModelCsvHeaderForm(request.POST)
        if form.is_valid():
            # model_file.first_header_dropdown = request.POST["first_header_dropdown"]
            # model_file.second_header_dropdown = request.POST["second_header_dropdown"]
            # model_file.third_header_dropdown = request.POST["third_header_dropdown"]
            form.save()
            # TODO change this redirect
            return redirect('bpmn-model-home')
    else:
        form = ModelCsvHeaderForm()
    return render(request, 'bpmn_app/bpmn_column_headers.html', {'form': form, 'case_id': case_id_col_name,
                                                                 'timestamp': timestamp_col_name,
                                                                 'activity': activity_col_name})




