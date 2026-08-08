import requests
from django.core.management.base import BaseCommand
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from articles.models import Article

class Command(BaseCommand):
    help = 'Seed all existing articles with unique, reliable images from Lorem Picsum'

    def handle(self, *args, **options):
        # Fetch all articles from the database
        articles = Article.objects.all()
        total_articles = articles.count()
        
        self.stdout.write(f"Found {total_articles} articles. Seeding with unique images...")
        
        seeded_count = 0
        skipped_count = 0
        
        for index, article in enumerate(articles):
            # 1. Skip if the article already has a user-uploaded image
            if article.image and article.image.name:
                self.stdout.write(f"[{index+1}/{total_articles}] Article '{article.title}' already has an image. Skipping.")
                skipped_count += 1
                continue
                
            # 2. Use the article's unique ID as the seed. 
            # Since IDs are unique, every article gets a DIFFERENT, permanent image.
            img_url = f"https://picsum.photos/seed/{article.id}/800/600"
            
            try:
                self.stdout.write(f"[{index+1}/{total_articles}] Fetching unique image for '{article.title}'...")
                
                # 3. Fetch the image
                response = requests.get(img_url)
                
                if response.status_code == 200:
                    # Create a temporary file to store the image
                    img_temp = NamedTemporaryFile(delete=True)
                    img_temp.write(response.content)
                    img_temp.flush()
                    
                    # 4. Save the image to the Django model
                    article.image.save(f"article_{article.id}.jpg", File(img_temp), save=True)
                    
                    seeded_count += 1
                    self.stdout.write(self.style.SUCCESS(f" -> Successfully added image to '{article.title}'"))
                else:
                    self.stdout.write(self.style.ERROR(f" -> Failed to fetch image for '{article.title}' (HTTP {response.status_code})"))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f" -> Error processing '{article.title}': {str(e)}"))
        
        # Final summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f"Seeding complete!"))
        self.stdout.write(f"Total articles processed: {total_articles}")
        self.stdout.write(f"New images added: {seeded_count}")
        self.stdout.write(f"Already had images (skipped): {skipped_count}")
        self.stdout.write("="*50)