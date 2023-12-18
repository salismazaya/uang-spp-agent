from __future__ import annotations
from django.conf import settings
from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentType, initialize_agent, tool
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import MessagesPlaceholder
from langchain.schema import SystemMessage
from langchain.embeddings import OpenAIEmbeddings
from langchain.callbacks import get_openai_callback
from dataclasses import dataclass
from core.models import Tagihan, Siswa, Payment, Kelas
from numpy.linalg import norm
import datetime, typing, midtransclient
import numpy as np, functools
import re

def replace_markdown_links(text):
    # Pola regex untuk mencari link Markdown
    markdown_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'

    # Fungsi penggantian
    def replace(match):
        link_text = match.group(1)
        link_url = match.group(2)
        return f'{link_text} ({link_url})'

    # Melakukan penggantian menggunakan regex
    replaced_text = re.sub(markdown_link_pattern, replace, text)

    return replaced_text

snap = midtransclient.Snap(
    is_production = not settings.DEBUG,
    server_key = settings.MIDTRANS_SERVER_KEY,
    client_key = settings.MIDTRANS_CLIENT_KEY
)

@dataclass
class KelasData:
    id: int
    nama_kelas: str

@dataclass
class Keren:
    id: int
    title: str
    jumlah: int

class Conversation:
    CONVERSATION = {}
    
    @classmethod
    def get_conversation(cls, key: str) -> Conversation:
        conversation = cls.CONVERSATION.get(key)
        if not conversation:
            cls.CONVERSATION[key] = Conversation(key)
            conversation = cls.CONVERSATION[key]
        
        return conversation

    def __init__(self, nomor_whatsapp: str):
        self.llm = ChatOpenAI(temperature = 0.3, max_tokens = 300)
        self.memory = ConversationBufferWindowMemory(k = 3, memory_key = 'memory', return_messages = True)
        self.time = datetime.datetime.now()
        self.nomor_whatsapp = nomor_whatsapp
        self.siswa = Siswa.objects.filter(nomor_whatsapp = nomor_whatsapp).first()
        self.showed = False

        def reqistered_required(func):
            @functools.wraps(func)
            def inner(*args, **kwargs):
                if not self.siswa:
                    return 'siswa belum terdaftar. beri tau user dia harus daftar dulu. biarkan siswa bertindak'
                
                return func(*args, **kwargs)
            
            return inner

        # @tool
        # def get_all_kelas() -> typing.List[KelasData]:
        #     "untuk mendapatkan seluruh kelas"
        #     kelass = Kelas.objects.all()
        #     rv = []
        #     for kelas in kelass:
        #         rv.append(
        #             KelasData(
        #                 id = kelas.pk,
        #                 nama_kelas = kelas.nama_kelas
        #             )
        #         )
            
        #     return rv

        # @tool
        # def get_kelas(kelas_id: int) -> KelasData:
        #     "untuk mendapatkan salah satu kelas"
        #     kelas = Kelas.objects.filter(pk = kelas_id).first()
        #     if not kelas:
        #         return 'kelas tidak ada'
            
        #     return KelasData(
        #         id = kelas_id,
        #         nama_kelas = kelas.nama_kelas
        #     )

        # @tool
        # def register(nama_siswa: str = None, kelas: KelasData = None) -> str:
        #     "untuk register. nama siswa dan kelas, hasil dari input user"

        #     if nama_siswa is None:
        #         return 'beri tau siswa bahwa namanya kosong. biarkan siswa beraksi'
            
        #     if kelas is None:
        #         return 'beri tau siswa bahwa kelasnya kosong. beri tau daftar kelasnya. biarkan siswa beraksi'

        #     self.siswa = Siswa()
        #     self.siswa.nama = nama_siswa
        #     self.siswa.kelas_id = kelas.id
        #     self.siswa.nomor_whatsapp = self.nomor_whatsapp
        #     self.siswa.save()

        #     self.memory.clear()
        #     return 'ok'

        @tool
        @reqistered_required
        def get_siswa_name():
            "untuk mendapatkan nama siswa"
            return 'nama siswa adalah ' + self.siswa.nama

        @tool
        @reqistered_required
        def how_to_pay():
            "jika siswa menanyakan bagaimana cara membayar tagihannya"
            return "beri tau siswa bahwa dia bisa melakukan pembayaran disini, di bot whatsapp. berikan konfirmasi ke siswa untuk melakukan pembayaran. jawab dengan singkat satu paragraf"

        @tool
        @reqistered_required
        def get_tunggakan(
            tahun_end: int = self.time.year,
            bulan_end: int = self.time.month,
            hari_end: int = self.time.day,
            tahun_start: int = 1970,
            bulan_start: int = 1,
            hari_start: int = 1,
            queries: typing.List[str] = None
        ) -> typing.Union[typing.List[Keren], str]:
            "untuk mendapatkan tunggakan yang belum dibayar oleh siswa."
            date_start = datetime.datetime(year = tahun_start, month = bulan_start, day = hari_start)
            date_end = datetime.datetime(year = tahun_end, month = bulan_end, day = hari_end)
            tagihan = Tagihan.get_tagihan_by_siswa(nomor_whatsapp).filter(time__gte = date_start).filter(time__lte = date_end)

            embedding = OpenAIEmbeddings()

            rv = []
            for x in tagihan:
                if not queries:
                    keren = Keren(id = x.pk, title = x.nama_tagihan, jumlah = x.jumlah_tagihan)
                    rv.append(keren)
                    continue

                for query in queries:
                    A = embedding.embed_query(query)
                    B = embedding.embed_query(x.nama_tagihan)
                    cosine = np.dot(A,B) / (norm(A) * norm(B))
                    if cosine > 0.8:
                        keren = Keren(id = x.pk, title = x.nama_tagihan, jumlah = x.jumlah_tagihan)
                        rv.append(keren)
            if rv:
                return rv

            return 'tidak ada tagihan'

        @tool
        @reqistered_required
        def bayar_tunggakan(tunggakans: typing.List[Keren] = None) -> str:
            """
            untuk bayar tunggakan
            """
            if not tunggakans:
                return 'tagihan yang mana?'
            
            # if not self.showed:
            #     self.showed = True
            #     return 'beri tau dulu siswa tersebut tentang tagihannya'
            
            payment = Payment()
            payment.nomor_whatsapp = self.nomor_whatsapp
            payment.save()
            amount = 0
            for x in tunggakans:
                tagihan = Tagihan.objects.get(pk = x.id)
                if tagihan.nama_tagihan != x.title:
                    return 'terdapat anomali batalkan transaksi. beri tau siswa bahwa terjadi error'
                
                amount += x.jumlah
                payment.tagihan.add(tagihan)


            param = {
                "transaction_details": {
                    "order_id": f"SYAHDA-{payment.pk}",
                    "gross_amount": amount
                }
            }

            transaction = snap.create_transaction(param)
            url = transaction['redirect_url']

            return f'link ini untuk membayar {url} dan juga jelaskan rinciannya ke siswa'

        self.tools = [get_tunggakan, bayar_tunggakan, get_siswa_name, how_to_pay]

        system_message = SystemMessage(content = f'sekarang tanggal {self.time.strftime("%d %B %Y")}. kamu adalah bendahara sekolah bernama Syahda, kamu dibuat oleh Salis Mazaya Miftah Malik seorang programmer jago yang berpengalamam selama 5 tahun. kamu sedang berinteraksi dengan siswa dia adalah seseorang yang gaptek jadi jelaskan dengan singkat dan jelas. siswa ingin membayar semua tagihan. anda sama seperti manusaia bisa melakukan kesalahan berikan disclaimer kepada siswa')

        self.agent_executor = initialize_agent(
            tools = self.tools, 
            llm = self.llm, 
            agent = AgentType.OPENAI_FUNCTIONS, 
            verbose = settings.DEBUG,
            handle_parsing_errors = True,
            agent_kwargs = {
                "system_message": system_message,
                "extra_prompt_messages": [MessagesPlaceholder(variable_name = "memory")],
            },
            memory = self.memory,
        )
    
    def __call__(self, text: str):
        with get_openai_callback() as cb:
            rv = replace_markdown_links(
                self.agent_executor.run(text)
            )
        if settings.DEBUG:
            print(cb)
        
        return rv