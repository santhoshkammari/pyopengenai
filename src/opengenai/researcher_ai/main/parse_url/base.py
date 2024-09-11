from abc import abstractmethod, ABC


class BaseHtmlParser(ABC):
    @abstractmethod
    def parse_html(self, urls: str) -> dict:
        pass