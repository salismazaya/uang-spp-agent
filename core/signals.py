from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from core.models import Tagihan, TagihanDibayar, Grup


@receiver(post_save, sender = TagihanDibayar)
def tagihan_dibayar_signal(sender, **kwargs):
    tagihan_dibayar: TagihanDibayar = kwargs['instance']
    tagihan: Tagihan = tagihan_dibayar.tagihan
    if tagihan_dibayar.dibayar:
        tagihan.sudah_bayar.add(tagihan_dibayar.siswa)
    else:
        tagihan.sudah_bayar.remove(tagihan_dibayar.siswa)


@receiver(post_save, sender = Tagihan)
def tagihan_signal(sender, **kwargs):
    tagihan: Tagihan = kwargs['instance']

    siswa = tagihan.siswa.all()
    for x in tagihan.grup.all():
        s = Grup.get_all_siswa(x.pk)
        siswa |= s
    
    for x in siswa:
        TagihanDibayar.objects.get_or_create(tagihan_id = tagihan.pk, siswa_id = x.pk)


@receiver(m2m_changed, sender = Tagihan.sudah_bayar.through)
def tagihan_signal_2(sender, **kwargs):
    if kwargs['action'] == 'post_add':
        tagihan: Tagihan = kwargs['instance']
        for siswa_id in kwargs['pk_set']:
            TagihanDibayar.objects.filter(tagihan__pk = tagihan.pk, siswa__pk = siswa_id).update(dibayar = True)


@receiver(m2m_changed, sender = Tagihan.siswa.through)
def tagihan_signal_3(sender, **kwargs):
    tagihan: Tagihan = kwargs['instance']
    for siswa_id in kwargs['pk_set']:
        TagihanDibayar.objects.get_or_create(tagihan_id = tagihan.pk, siswa_id = siswa_id)


@receiver(m2m_changed, sender = Tagihan.grup.through)
def tagihan_signal_4(sender, **kwargs):
    tagihan: Tagihan = kwargs['instance']

    siswas = None
    for x in kwargs['pk_set']:
        s = Grup.get_all_siswa(x)
        if siswas is None:
            siswas = s
        else:
            siswas |= s

    for siswa in siswas:
        TagihanDibayar.objects.get_or_create(tagihan_id = tagihan.pk, siswa_id = siswa.pk)
