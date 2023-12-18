from django.db import models
from django.utils import timezone

class Payment(models.Model):
    tagihan = models.ManyToManyField('core.Tagihan')
    nomor_whatsapp = models.CharField(max_length = 30)

class Grup(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = 'Grup'
    nama = models.CharField(max_length = 255)
    parent_grup = models.ManyToManyField('core.Grup', blank = True)
    siswa = models.ManyToManyField('core.Siswa', blank = True)

    @staticmethod
    def get_all_siswa(group_id: int):
        def recursively_get_siswa(group):
            all_siswa = group.siswa.all()
            for parent_group in group.parent_grup.exclude(pk = group.pk):
                all_siswa |= recursively_get_siswa(parent_group)
            return all_siswa

        try:
            group = Grup.objects.get(pk=group_id)
            rv = recursively_get_siswa(group)
            return rv
        except Grup.DoesNotExist:
            return None

    def __str__(self):
        return self.nama

class Kelas(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = 'Kelas'
    
    nama_kelas = models.CharField(max_length = 255)

    def __str__(self):
        return self.nama_kelas

class Siswa(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = 'Siswa'

    nama = models.CharField(max_length = 255)
    kelas = models.ForeignKey(Kelas, on_delete = models.PROTECT)
    nomor_whatsapp = models.CharField(max_length = 20)

    def __str__(self):
        return self.nama

class Tagihan(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = 'Tagihan'

    nama_tagihan = models.CharField(max_length = 255)
    grup = models.ManyToManyField(Grup, blank = True)
    siswa = models.ManyToManyField(Siswa, blank = True)
    sudah_bayar = models.ManyToManyField(Siswa, blank = True, related_name = 'sekeren')
    jumlah_tagihan = models.PositiveIntegerField()
    time = models.DateField(default = timezone.now, verbose_name = 'Waktu')
    
    def __str__(self):
        return self.nama_tagihan

    @staticmethod
    def get_tagihan_by_siswa(nomor_whatsapp: str):
        tagihan_list = Tagihan.objects.filter(
            models.Q(siswa__nomor_whatsapp = nomor_whatsapp) |
            models.Q(grup__siswa__nomor_whatsapp = nomor_whatsapp)
        ).exclude(sudah_bayar__nomor_whatsapp = nomor_whatsapp).distinct()
        return tagihan_list

class TagihanDibayar(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = 'Pembayaran'
        unique_together = ('siswa', 'tagihan')
    
    tagihan = models.ForeignKey(Tagihan, on_delete = models.PROTECT)
    siswa = models.ForeignKey(Siswa, on_delete = models.PROTECT)
    dibayar = models.BooleanField(default = False, verbose_name = 'Dibayar')