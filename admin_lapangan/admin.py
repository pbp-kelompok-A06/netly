from django.contrib import admin
from .models import Lapangan, JadwalLapangan

# Register your models here.
@admin.register(Lapangan)
class LapanganAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'price', 'admin_lapangan', 'created_at', 'updated_at')
    list_filter = ('location', 'created_at', 'admin_lapangan')
    search_fields = ('name', 'location', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Informasi Dasar', {
            'fields': ('id', 'name', 'location', 'description')
        }),
        ('Harga & Gambar', {
            'fields': ('price', 'image')
        }),
        ('Admin & Waktu', {
            'fields': ('admin_lapangan', 'created_at', 'updated_at')
        }),
    )

@admin.register(JadwalLapangan)
class JadwalLapanganAdmin(admin.ModelAdmin):
    list_display = ('lapangan', 'tanggal', 'start_main', 'end_main', 'is_available', 'created_at')
    list_filter = ('is_available', 'tanggal', 'lapangan')
    search_fields = ('lapangan__name',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('tanggal', 'start_main')
    
    fieldsets = (
        ('Informasi Jadwal', {
            'fields': ('id', 'lapangan', 'tanggal')
        }),
        ('Waktu Main', {
            'fields': ('start_main', 'end_main', 'is_available')
        }),
        ('Timestamp', {
            'fields': ('created_at', 'updated_at')
        }),
    )