"""model.src.data package."""
from model.src.data.ingest import ingest
from model.src.data.preprocess import preprocess
from model.src.data.split import split, stratified_split

__all__ = ["ingest", "preprocess", "split", "stratified_split"]
