from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.views import View

from application.use_cases.convert_currency import ConvertCurrencyUseCase
from domain.exceptions import DomainError
from infrastructure.django_app.repositories import DjangoExchangeRateRepository
from infrastructure.parser.query_parser import QueryParser


class ConvertMoneyView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        query = request.GET.get("query")
        if not query:
            return HttpResponseBadRequest("Query parameter is required")

        try:
            parsed_query = QueryParser().parse(query)
            use_case = ConvertCurrencyUseCase(DjangoExchangeRateRepository())
            result = use_case.execute(
                parsed_query.amount, parsed_query.source_currency, parsed_query.target_currency
            )
        except DomainError as exc:
            return HttpResponseBadRequest(str(exc))

        answer = (
            f"{result.source.amount} {result.source.currency.code} = "
            f"{result.converted.amount} {result.converted.currency.code}"
        )
        return JsonResponse({"answer": answer})
