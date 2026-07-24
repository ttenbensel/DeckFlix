
from deckflix_app.library_manager import scan_all_libraries
from deckflix_app.services.file_hash import sha256_file
from deckflix_app.models.media import IndexedMedia



class MediaIndex:
    """
    Central media catalogue for DeckFlix.

    Every module should query this object instead of scanning
    the filesystem independently.
    """

    def confirm_exact_movie_duplicates(self):
        """
        Hash same-title, same-year and same-size candidates.

        Nothing is moved or deleted.
        """

        confirmed = []

        for key, items in self.find_movie_duplicates().items():
            size_groups = {}

            for item in items:
                if item.size <= 0:
                    continue

                size_groups.setdefault(item.size, []).append(item)

            for size, candidates in size_groups.items():
                if len(candidates) < 2:
                    continue

                hash_groups = {}

                for item in candidates:
                    try:
                        digest = sha256_file(item.path)
                    except OSError:
                        continue

                    hash_groups.setdefault(digest, []).append(item)

                for digest, matches in hash_groups.items():
                    if len(matches) > 1:
                        confirmed.append(
                            {
                                "key": key,
                                "size": size,
                                "sha256": digest,
                                "items": matches,
                            }
                        )

        return confirmed

    def __init__(self):
        self.movies = []
        self.tv = []

    def rebuild(self):
        self.movies.clear()
        self.tv.clear()

        results = scan_all_libraries()

        for library_name, result in results.items():
            if result["scan"] is None:
                continue

            for item in result["scan"]["movie_items"]:
                self.movies.append(
                    IndexedMedia(
                        title=item.title,
                        media_type="movie",
                        library=library_name,
                        path=item.path,
                        resolution=item.resolution,
                        year=item.year,
			size=item.path.stat().st_size if item.path.exists() else 0,
                    )
                )

            for item in result["scan"]["tv_items"]:
                self.tv.append(
                    IndexedMedia(
                        title=item.title,
                        media_type="tv",
                        library=library_name,
                        path=item.path,
                        resolution=item.resolution,
                        year=item.year,	
			size=item.path.stat().st_size if item.path.exists() else 0,
                    )
                )
    def classify_movie_duplicates(self):
        """
        Classify duplicate candidates without modifying any files.
        """

        results = []

        for key, items in self.find_movie_duplicates().items():
            sizes = {item.size for item in items}
            resolutions = {item.resolution for item in items}

            if len(sizes) == 1:
                classification = "Likely exact copy"
            elif len(resolutions) > 1:
                classification = "Different quality versions"
            else:
                classification = "Needs review"

            results.append(
                {
                    "key": key,
                    "classification": classification,
                    "items": items,
                }
            )

        return results
    @property
    def movie_count(self):
        return len(self.movies)

    @property
    def tv_count(self):
        return len(self.tv)

    def summary(self):
        return {
            "movies": self.movie_count,
            "tv": self.tv_count,
        }
    def find_movie(self, title):
        """
        Find movies containing the supplied title, case-insensitively.
        """

        search = title.strip().lower()

        return [
            movie
            for movie in self.movies
            if search in movie.title.lower()
        ]


    def find_tv(self, title):
        """
        Find TV items containing the supplied title, case-insensitively.
        """

        search = title.strip().lower()

        return [
            item
            for item in self.tv
            if search in item.title.lower()
        ]


    def find_by_library(self, library_name):
        """
        Return all indexed media stored in a named library.
        """

        search = library_name.strip().lower()

        return [
            item
            for item in self.movies + self.tv
            if item.library.lower() == search
        ]


    def find_movie_duplicates(self):
        """
        Return movie groups sharing the same normalised duplicate key.
        """

        groups = {}

        for movie in self.movies:
            groups.setdefault(movie.duplicate_key, []).append(movie)

        return {
            key: items
            for key, items in groups.items()
            if len(items) > 1
        }

    def duplicate_summary(self, limit=10):
        """
        Return a readable, safely sorted sample of duplicate movie groups.
        """

        duplicates = self.find_movie_duplicates()

        ordered = sorted(
            duplicates.items(),
            key=lambda entry: (
                entry[0][0] or "",
                entry[0][1] if entry[0][1] is not None else 0,
            ),
        )

        return ordered[:limit]
