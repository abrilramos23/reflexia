from django.db import connection
from django.http import JsonResponse


def test_db(request):
    """Raw query against the Usuari table (mirrors the old Express route)."""
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM "Usuari"')
            columns = [col[0] for col in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return JsonResponse(rows, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
