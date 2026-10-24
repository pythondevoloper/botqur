from django.urls import path

from . import views

app_name = "botqur"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path(
        "musobaqalar/<slug:slug>/",
        views.MusobaqaDetailView.as_view(),
        name="musobaqa-detail",
    ),
    path(
        "robotlar/<slug:slug>/",
        views.RobotDetailView.as_view(),
        name="robot-detail",
    ),
    path("api/murojaat/", views.contact_submit, name="contact-submit"),
    path("api/nizom/<slug:slug>/", views.nizom_detail, name="nizom-detail"),
    path("api/robotlar/", views.robotlar_list, name="robotlar-list"),
    path("api/robotlar/<slug:slug>/", views.robotlar_detail, name="robotlar-detail"),
    path("api/musobaqalar/", views.musobaqalar_list, name="musobaqalar-list"),
    path(
        "api/musobaqalar/<slug:slug>/",
        views.musobaqalar_detail,
        name="musobaqalar-detail",
    ),
    path("api/hero-3d/", views.hero_3d_model, name="hero-3d-model"),
    path("robots.txt", views.robots_txt, name="robots-txt"),
    path("sitemap.xml", views.sitemap_xml, name="sitemap-xml"),
]
