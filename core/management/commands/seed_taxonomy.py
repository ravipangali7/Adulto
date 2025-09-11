from django.core.management.base import BaseCommand
from django.utils.text import slugify

from core.models import Category, Tag


class Command(BaseCommand):
	help = 'Seed popular adult categories and tags (idempotent)'

	def handle(self, *args, **options):
		categories = [
			"Amateur", "Anal", "Asian", "BBW", "Big Ass", "Big Tits", "Blonde",
			"Blowjob", "Bondage", "Brazilian", "British", "Brunette", "Cartoon",
			"College", "Compilation", "Cougar", "Creampie", "Cuckold", "Cumshot",
			"DP", "Ebony", "European", "Facial", "Fetish", "Fisting", "Gangbang",
			"German", "Hardcore", "HD", "Indian", "Interracial", "Japanese",
			"Korean", "Latina", "Lesbian", "Massage", "Masturbation", "MILF",
			"POV", "Public", "Redhead", "Rough", "Russian", "SFW", "Squirting",
			"Step Fantasy", "Teen", "Threesome", "VR", "Webcam"
		]

		tags = [
			"verified", "new", "trending", "popular", "hd", "4k", "asmr", "pov",
			"cosplay", "outdoor", "office", "teacher", "nurse", "fitness",
			"tattoo", "piercing", "natural", "shaved", "oiled", "solo", "toy",
			"quickie", "romantic", "rough", "slow", "creampie", "facial",
			"stepmom", "stepsis", "teen-18", "milf", "anal", "lesbian", "threesome",
			"dp", "gangbang", "webcam", "live", "compilation", "orgasm"
		]

		created_cats = 0
		for name in categories:
			slug = slugify(name)
			obj, created = Category.objects.get_or_create(slug=slug, defaults={"name": name})
			if not created and obj.name != name:
				obj.name = name
				obj.save(update_fields=["name"])
			created_cats += 1 if created else 0

		created_tags = 0
		for name in tags:
			slug = slugify(name)
			obj, created = Tag.objects.get_or_create(slug=slug, defaults={"name": name})
			if not created and obj.name != name:
				obj.name = name
				obj.save(update_fields=["name"])
			created_tags += 1 if created else 0

		self.stdout.write(self.style.SUCCESS(
			f"Seeded categories (new: {created_cats}) and tags (new: {created_tags})."
		))


