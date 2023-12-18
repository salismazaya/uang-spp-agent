from django.contrib import admin
from django.http.request import HttpRequest
from core.models import Grup, Siswa, Tagihan, Kelas, TagihanDibayar

class TagihanAdmin(admin.ModelAdmin):
    list_display = ('nama_tagihan', 'time')
    search_fields = ('nama_tagihan',)
    readonly_fields = ('sudah_bayar',)

class TagihanFilter(admin.SimpleListFilter):
    title = 'Tagihan'
    parameter_name = 'tagihan'

    def lookups(self, request, model_admin):
        rv = []
        for tagihan in Tagihan.objects.all():
            rv.append((tagihan.pk, tagihan.nama_tagihan))
        
        return rv
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(tagihan__pk = self.value())
        
        return queryset

class KelasFilter(admin.SimpleListFilter):
    title = 'Kelas'
    parameter_name = 'kelas'

    def lookups(self, request, model_admin):
        rv = []
        for tagihan in Kelas.objects.all():
            rv.append((tagihan.pk, tagihan.nama_kelas))
        
        return rv
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(siswa__kelas__pk = self.value())
        
        return queryset

class TagihanDibayarAdmin(admin.ModelAdmin):
    search_fields = ('siswa__nama',)
    list_display = ('id', 'tagihan', 'jumlah_tagihan', 'siswa', 'kelas', 'waktu', 'dibayar')
    list_filter = (TagihanFilter, KelasFilter, 'tagihan__time', 'dibayar')

    def kelas(self, obj: TagihanDibayar):
        return obj.siswa.kelas

    def jumlah_tagihan(self, obj: TagihanDibayar):
        return obj.tagihan.jumlah_tagihan

    def waktu(self, obj: TagihanDibayar):
        return obj.tagihan.time
    
    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

admin.site.register(Siswa)
admin.site.register(Grup)
admin.site.register(Tagihan, TagihanAdmin)
admin.site.register(Kelas)
admin.site.register(TagihanDibayar, TagihanDibayarAdmin)