from django.shortcuts import render

# Dummy data untuk lapangan
court_list = [
    {"name": "Court A", "price": 50000, "image": "https://blog.khelomore.com/wp-content/uploads/2022/02/MC44MjUxMzYwMCAxNDY4MjI1Njg3.jpeg"},
    {"name": "Court B", "price": 60000, "image": "https://img.olympics.com/images/image/private/t_s_16_9_g_auto/t_s_w960/f_auto/primary/kfsyzuaoipfhm4qonqci"},
]

# Dummy data untuk carousel event
event_list = [
    {"name": "Event 1", "image": "https://cdn.mos.cms.futurecdn.net/T94A6VdniJsaCYaUFsCPWk.jpg"},
    {"name": "Event 2", "image": "https://c8.alamy.com/comp/2PE3H69/a-general-view-of-play-on-day-two-of-the-yonex-all-england-open-badminton-championships-at-the-utilita-arena-birmingham-picture-date-wednesday-march-15-2023-2PE3H69.jpg"},
    {"name": "Event 3", "image": "https://images.cnbctv18.com/wp-content/uploads/2018/04/2018_4img09_Apr_2018_PTI4_9_2018_000149B.jpg"},
]

def index(request):
    return render(request, 'homepage/index.html', {
        "court_list": court_list,
        "event_list": event_list,
    })
