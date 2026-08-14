"""Django Admin 的只读运维页面。"""

from datetime import date

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse

from .forms import SystemLogFilterForm
from .log_reader import LogEvent, read_log_events


def _matches_filters(event: LogEvent, filters: SystemLogFilterForm) -> bool:
    """判断事件是否满足已清洗的 Admin 查询条件。"""
    selected_date: date | None = filters.cleaned_data["date"]
    level: str = filters.cleaned_data["level"]
    event_name: str = filters.cleaned_data["event"]
    status: int | None = filters.cleaned_data["status"]
    request_id: str = filters.cleaned_data["request_id"]
    timestamp = str(event.get("timestamp", ""))
    return (
        (selected_date is None or timestamp.startswith(selected_date.isoformat()))
        and (not level or event.get("level") == level)
        and (not event_name or event_name.casefold() in str(event.get("event", "")).casefold())
        and (status is None or event.get("status") == status)
        and (not request_id or request_id in str(event.get("request_id", "")))
    )


def system_logs(request: HttpRequest) -> HttpResponse:
    """展示最多五千条日志，并以五十条为一页过滤浏览。"""
    if not getattr(get_user(request), "is_superuser", False):
        raise PermissionDenied
    form = SystemLogFilterForm(request.GET)
    events = read_log_events(settings.LOG_DIR)
    if form.is_valid():
        events = [event for event in events if _matches_filters(event, form)]
    paginator = Paginator(events, 50)
    page = paginator.get_page(request.GET.get("page"))
    query = request.GET.copy()
    query.pop("page", None)
    context = {
        **admin.site.each_context(request),
        "title": "系统日志",
        "form": form,
        "events": page.object_list,
        "page_obj": page,
        "filter_query": query.urlencode(),
    }
    return TemplateResponse(request, "admin/system_logs.html", context)
