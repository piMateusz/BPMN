from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.urls import reverse

from .forms import ModelFormWithFileField
from .models import BpmnFile
from .bpmn_utils.graph import display_bpmn_model
from .bpmn_utils.w_net import load_df_columns_from_file

import os
from difflib import SequenceMatcher

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

    df_columns = load_df_columns_from_file(file_path)

    case_id_col_name = "Case ID"
    timestamp_col_name = "Start Timestamp"
    activity_col_name = "Activity"

    case_id_matching_probabilities = [SequenceMatcher(None, case_id_col_name, df_column).ratio() for df_column in df_columns]
    timestamp_matching_probabilities = [SequenceMatcher(None, timestamp_col_name, df_column).ratio() for df_column in df_columns]
    activity_matching_probabilities = [SequenceMatcher(None, activity_col_name, df_column).ratio() for df_column in df_columns]

    case_id_max_prob = max(case_id_matching_probabilities)
    case_id_df_idx = case_id_matching_probabilities.index(case_id_max_prob)
    case_id_df_val = df_columns[case_id_df_idx]

    timestamp_max_prob = max(timestamp_matching_probabilities)
    timestamp_df_idx = timestamp_matching_probabilities.index(timestamp_max_prob)
    timestamp_df_val = df_columns[timestamp_df_idx]

    activity_max_prob = max(activity_matching_probabilities)
    activity_df_idx = activity_matching_probabilities.index(activity_max_prob)
    activity_df_val = df_columns[activity_df_idx]

    if request.method == 'POST':
        model_file.caseID = request.POST["caseID"]
        model_file.timestamp = request.POST["timestamp"]
        model_file.activity = request.POST["activity"]
        model_file.save()
        return redirect('bpmn-model-home')

    return render(request, 'bpmn_app/bpmn_column_headers.html', {'df_columns': df_columns,
                                                                 'case_id_df_val': case_id_df_val,
                                                                 'timestamp_df_val': timestamp_df_val,
                                                                 'activity_df_val': activity_df_val,
                                                                 'case_id_max_prob': round(case_id_max_prob*100, 2),
                                                                 'timestamp_max_prob': round(timestamp_max_prob*100, 2),
                                                                 'activity_max_prob': round(activity_max_prob*100, 2)})




