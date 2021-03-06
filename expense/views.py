import csv

import xlwt
from core.constants import current_month
from django.http import Http404
from django.http.response import HttpResponse
from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from xhtml2pdf import pisa

from .models import Expense
from .serializers import ExpenseSerializer


class ExpenseListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            results = (
                Expense.objects.filter(user=request.user)
                .filter(date__month=str(current_month))
                .order_by("-id")
            )
            serializer = ExpenseSerializer(results, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except:
            return Response(
                data={"message": "Unable to retrieve expenses"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def post(self, request):
        try:
            data = request.data
            expense = Expense.objects.create(
                name=data["name"],
                amount=data["amount"],
                description=data["description"],
                category_id=data["category"],
                user=request.user,
            )
            serializer = ExpenseSerializer(expense, many=False)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except:
            return Response(
                data={"message": "Unable to create expense"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ExpenseDetailView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        try:
            return Expense.objects.get(pk=pk)
        except Expense.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        expense = self.get_object(pk)
        if request.user == expense.user:
            serializer = ExpenseSerializer(expense)
            return Response(serializer.data)
        else:
            return Response(
                data={"message": "Forbidden, Not Authorized"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

    def put(self, request, pk):
        expense = self.get_object(pk)
        data = request.data
        if request.user == expense.user:
            expense.name = data["name"]
            expense.amount = data["amount"]
            expense.description = data["description"]
            expense.category_id = data["category"]
            serializer = ExpenseSerializer(expense, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
        else:
            return Response(
                data={"message": "Forbidden, Not Authorized"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

    def delete(self, request, pk):
        expense = self.get_object(pk)
        if request.user == expense.user:
            expense.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                data={"message": "Forbidden, Not Authorized"},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class ExportExpenseCsv(APIView):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=expenses.csv"
        writer = csv.writer(response)
        writer.writerow(["name", "category", "amount", "description"])
        expenses = (
            Expense.objects.filter(user=request.user)
            .filter(date__month=str(current_month))
            .order_by("-id")
        )
        for expense in expenses:
            writer.writerow(
                [
                    expense.name,
                    expense.category.name,
                    expense.amount,
                    expense.description,
                ]
            )
        return response


# pipenv xlwt
class ExportExpenseExcel(APIView):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="application/ms-excel")
        response["Content-Disposition"] = "attachment; filename=expenses.xls"
        wb = xlwt.Workbook(encoding="utf-8")
        ws = wb.add_sheet("Expenses")
        row_num = 0
        font_style = xlwt.XFStyle()
        font_style.font.bold = True
        columns = ["name", "category", "amount", "description"]
        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style)
        font_style = xlwt.XFStyle()
        rows = (
            Expense.objects.filter(user=request.user)
            .filter(date__month=str(current_month))
            .order_by("-id")
            .values_list("name", "category_id", "amount", "description")
        )
        for row in rows:
            row_num += 1
            for col_num in range(len(row)):
                ws.write(row_num, col_num, str(row[col_num]), font_style)
        wb.save(response)
        return response


# pipenv install xhtml2pdf
# https://stackoverflow.com/questions/50384613/pdf-in-django-rest-framework
class ExportExpensePdf(APIView):
    def get(self, request, *args, **kwargs):
        expenses = (
            Expense.objects.filter(user=request.user)
            .filter(date__month=str(current_month))
            .order_by("-id")
        )
        template_path = "expenses.html"
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = "attachment; filename=expenses.pdf"
        html = render_to_string(template_path, {"expenses": expenses})
        pisaStatus = pisa.CreatePDF(html, dest=response)
        return response
