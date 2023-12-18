from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from urllib.parse import parse_qs
from core.ai import Conversation
from core.models import Payment, Tagihan, Siswa
import requests, json, midtransclient

core = midtransclient.CoreApi(
    is_production = not settings.DEBUG,
    server_key = settings.MIDTRANS_SERVER_KEY,
    client_key = settings.MIDTRANS_CLIENT_KEY
)

@require_POST
@csrf_exempt
def webhook(request: HttpRequest):
    parsed_data = parse_qs(request.body.decode('utf-8'))
    result = {key: value[0] for key, value in parsed_data.items()}
    
    nowa = result['data[phone]'].replace('+62', '0', 1)
    conversation = Conversation.get_conversation(nowa)

    chat = {
        "secret": settings.WHAPIFY_API_KEY,
        "account": 157,
        "recipient": nowa,
        "type": "text",
        "message": conversation(result['data[message]'])
    }

    r = requests.post("https://whapify.id/api/send/whatsapp", params = chat)
    result = r.json()
    return HttpResponse('!')

@require_POST
@csrf_exempt
def midtrans_webhook(request: HttpRequest):
    data = json.loads(request.body)
    transaction = core.transactions.status(data['transaction_id'])
    order_id = data['order_id'].removeprefix('SYAHDA-')
    payment = Payment.objects.get(pk = order_id)

    if transaction['transaction_status'] == 'settlement':
        chat = {
            "secret": settings.WHAPIFY_API_KEY,
            "account": 157,
            "recipient": payment.nomor_whatsapp,
            "type": "text",
            "message": "Pembayaran kamu sudah kami terima :)"
        }

        siswa = Siswa.objects.get(nomor_whatsapp = payment.nomor_whatsapp)
        tagihan_tagihan = payment.tagihan.all()
        for tagihan in tagihan_tagihan:
            tagihan: Tagihan = tagihan
            tagihan.sudah_bayar.add(siswa)
        
        requests.post("https://whapify.id/api/send/whatsapp", params = chat)

    return HttpResponse('!')