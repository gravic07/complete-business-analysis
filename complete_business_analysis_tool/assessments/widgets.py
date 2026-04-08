from django.forms.widgets import RadioSelect


class RankedRadioSelect(RadioSelect):
    """RadioSelect that shows a rank badge beside each option.

    Pass option_ranks={str(pk): rank_int} so the widget can inject rank
    into the option template context as widget.rank.
    """

    template_name = "widgets/ranked_radio.html"
    option_template_name = "widgets/ranked_radio_option.html"

    def __init__(self, *args, option_ranks=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.option_ranks = dict(option_ranks) if option_ranks else {}

    def create_option(  # noqa: PLR0913
        self,
        name,
        value,
        label,
        selected,
        index,
        subindex=None,
        attrs=None,
    ):
        option = super().create_option(
            name,
            value,
            label,
            selected,
            index,
            subindex=subindex,
            attrs=attrs,
        )
        option["rank"] = self.option_ranks.get(str(value), "")
        return option
