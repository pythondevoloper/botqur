"""
BotQur statik sahifalari uchun Django view'lar.
"""

import json
import re

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView

from .models import (
    ContactRequest,
    MusobaqaNizom,
    Robot,
    MUSOBAQA_CHOICES,
    Musobaqa,
    BoshSahifaSozlamalari,
)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class HomeView(TemplateView):
    template_name = "botqur/home.html"


class NotFoundView(TemplateView):
    template_name = "botqur/404.html"


MUSOBAQA_SLUGS = {slug for slug, _ in MUSOBAQA_CHOICES}

ROBOT_SLUGS: set[str] = set()  # endi ishlatilmaydi — moslik uchun bo'sh qoldirildi.


class MusobaqaDetailView(TemplateView):
    def get_template_names(self):
        slug = self.kwargs["slug"]
        if slug not in MUSOBAQA_SLUGS:
            from django.http import Http404

            raise Http404  # handler404: 404 holati bilan (Google uni sahifa deb hisoblamaydi)
        else:
            self.template_name = f"botqur/musobaqalar/{slug}.html"
        return [self.template_name]


class RobotDetailView(TemplateView):
    template_name = "botqur/robotlar/shell.html"


# Ism uchun ruxsat etilgan belgilar: harf, bo'sh joy, apostrof, nuqta,
# chiziqcha. `[^\W\d_]` — Unicode harf (lotin ham, kirill ham); raqam va
# pastki chiziq bunga kirmaydi. Brauzerda ham shunday filtr bor, lekin u
# faqat qulaylik uchun — API'ga to'g'ridan-to'g'ri so'rov yuborilsa,
# tekshiruv shu yerda ishlaydi.
ISM_BELGILARI = re.compile(r"^(?:[^\W\d_]|[ '\u2019\u02bb.\-])+$")
ISM_HARF = re.compile(r"[^\W\d_]")


@require_POST
def contact_submit(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "Noto'g'ri so'rov."}, status=400)

    ism = (data.get("ism") or "").strip()
    telefon = (data.get("telefon") or "").strip()
    xabar = (data.get("xabar") or "").strip()
    robot = (data.get("robot") or "").strip()

    if not ism or not telefon:
        return JsonResponse(
            {"ok": False, "error": "Ism va telefon raqami majburiy."}, status=400
        )

    if not ISM_BELGILARI.fullmatch(ism) or not ISM_HARF.search(ism):
        return JsonResponse(
            {"ok": False, "error": "Ismda raqam yoki maxsus belgi bo'lmasligi kerak."},
            status=400,
        )

    telefon_raqamlari = re.sub(r"[\s\-()]", "", telefon)
    if not re.fullmatch(r"(\+?998)?\d{9}", telefon_raqamlari):
        return JsonResponse(
            {"ok": False, "error": "Telefon raqami noto'g'ri kiritildi."}, status=400
        )

    if len(ism) > 150 or len(telefon) > 32 or len(robot) > 150 or len(xabar) > 2000:
        return JsonResponse({"ok": False, "error": "Ma'lumot juda uzun."}, status=400)

    ContactRequest.objects.create(ism=ism, telefon=telefon, xabar=xabar, robot=robot)

    return JsonResponse({"ok": True})


@require_GET
def nizom_detail(request, slug):
    if slug not in MUSOBAQA_SLUGS:
        return JsonResponse({"available": False}, status=404)

    nizom = MusobaqaNizom.objects.filter(slug=slug).first()
    if nizom is None or not nizom.fayl:
        return JsonResponse({"available": False})

    return JsonResponse({"available": True, "url": nizom.fayl.url})


MUSOBAQA_NAMES = dict(MUSOBAQA_CHOICES)


def _robot_summary(robot: Robot) -> dict:
    return {
        "slug": robot.slug,
        "nomi": robot.nomi,
        "musobaqa_slug": robot.musobaqa,
        "musobaqa_nomi": MUSOBAQA_NAMES.get(robot.musobaqa, robot.musobaqa),
        "narxi": robot.narxi,
        "qisqa_tavsif": robot.qisqa_tavsif,
        "qismlari": robot.qismlari_royxati(),
        "muqova_url": robot.muqova_rasm.url if robot.muqova_rasm else None,
    }


@require_GET
def robotlar_list(request):
    robots = Robot.objects.filter(faol=True)
    return JsonResponse({"robotlar": [_robot_summary(r) for r in robots]})


@require_GET
def robotlar_detail(request, slug):
    robot = Robot.objects.filter(slug=slug, faol=True).first()
    if robot is None:
        return JsonResponse({"found": False}, status=404)

    rasmlar = [r.rasm.url for r in robot.rasmlar.all() if r.rasm]

    data = _robot_summary(robot)
    data.update(
        {
            "found": True,
            "afzalliklari": robot.afzalliklari_royxati(),
            "qismlari": robot.qismlari_royxati(),
            "video_url": robot.video.url if robot.video else None,
            "model_3d_url": robot.model_3d.url if robot.model_3d else None,
            "rasmlar": rasmlar,
        }
    )
    return JsonResponse(data)


def _musobaqa_data(m: Musobaqa) -> dict:
    return {
        "slug": m.slug,
        "nomi": MUSOBAQA_NAMES.get(m.slug, m.slug),
        "format": m.format,
        "yosh_oraligi": m.yosh_oraligi,
        "tavsif": m.tavsif,
        "jadval": m.jadval,
        "manzil": m.manzil,
        "muqova_url": m.muqova_rasm.url if m.muqova_rasm else None,
        "video_url": m.video.url if m.video else None,
    }


@require_GET
def musobaqalar_list(request):
    items = Musobaqa.objects.all()
    return JsonResponse({"musobaqalar": [_musobaqa_data(m) for m in items]})


@require_GET
def musobaqalar_detail(request, slug):
    if slug not in MUSOBAQA_SLUGS:
        return JsonResponse({"found": False}, status=404)

    m = Musobaqa.objects.filter(slug=slug).first()
    if m is None:
        return JsonResponse({"found": False}, status=404)

    data = _musobaqa_data(m)
    data["found"] = True
    data["rasmlar"] = [r.rasm.url for r in m.rasmlar.all() if r.rasm]
    return JsonResponse(data)


@require_GET
def hero_3d_model(request):
    sozlamalar = BoshSahifaSozlamalari.objects.first()
    if sozlamalar is None or not sozlamalar.hero_3d_model:
        return JsonResponse({"available": False})
    return JsonResponse({"available": True, "url": sozlamalar.hero_3d_model.url})


# --- 404, robots.txt, sitemap.xml (Google indekslashi uchun) -------------------------------

SAYT = "https://botqur.uz"


def not_found(request, exception=None):
    from django.shortcuts import render

    return render(request, "botqur/404.html", status=404)


@require_GET
def robots_txt(request):
    from django.http import HttpResponse

    matn = "User-agent: *\nAllow: /\nDisallow: /api/\n\nSitemap: " + SAYT + "/sitemap.xml\n"
    return HttpResponse(matn, content_type="text/plain; charset=utf-8")


@require_GET
def sitemap_xml(request):
    from django.http import HttpResponse

    manzillar = [SAYT + "/"]
    manzillar += [f"{SAYT}/musobaqalar/{slug}/" for slug in sorted(MUSOBAQA_SLUGS)]
    manzillar += [
        f"{SAYT}/robotlar/{slug}/"
        for slug in Robot.objects.filter(faol=True).order_by("slug").values_list("slug", flat=True)
    ]
    qatorlar = "".join(f"  <url><loc>{m}</loc></url>\n" for m in manzillar)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + qatorlar
        + "</urlset>\n"
    )
    return HttpResponse(xml, content_type="application/xml; charset=utf-8")
