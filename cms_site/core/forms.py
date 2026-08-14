"""核心运维界面的输入表单。"""

from django import forms

LOG_LEVEL_CHOICES = (
    ("", "全部级别"),
    ("DEBUG", "DEBUG"),
    ("INFO", "INFO"),
    ("WARNING", "WARNING"),
    ("ERROR", "ERROR"),
    ("CRITICAL", "CRITICAL"),
)


class SystemLogFilterForm(forms.Form):
    """解析系统日志列表允许的五个过滤条件。"""

    date = forms.DateField(
        label="日期",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    level = forms.ChoiceField(label="级别", required=False, choices=LOG_LEVEL_CHOICES)
    event = forms.CharField(label="事件", required=False, max_length=100)
    status = forms.IntegerField(label="状态码", required=False, min_value=100, max_value=599)
    request_id = forms.CharField(label="请求 ID", required=False, max_length=64)
