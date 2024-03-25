from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from core.models import Payment, Tagihan, Siswa
import json, midtransclient

core = midtransclient.CoreApi(
    is_production = not settings.DEBUG,
    server_key = settings.MIDTRANS_SERVER_KEY,
    client_key = settings.MIDTRANS_CLIENT_KEY
)


@require_POST
@csrf_exempt
def midtrans_webhook(request: HttpRequest):
    data = json.loads(request.body)
    transaction = core.transactions.status(data['transaction_id'])
    order_id = data['order_id'].removeprefix('SYAHDA-')
    payment = Payment.objects.get(pk = order_id)

    if transaction['transaction_status'] == 'settlement':
        siswa = Siswa.objects.get(nomor_whatsapp = payment.nomor_whatsapp)
        tagihan_tagihan = payment.tagihan.all()
        for tagihan in tagihan_tagihan:
            tagihan: Tagihan = tagihan
            tagihan.sudah_bayar.add(siswa)

    return HttpResponse('!')