"""
Text label management and markdown parsing.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Union, Literal, Optional, Dict
import re


def _parse_timestamp(timestamp_value) -> datetime:
    """
    Parse a timestamp value from configuration (ISO 8601 string or Unix epoch number).

    Args:
        timestamp_value: Raw 'timestamp' value from a text_labels entry

    Returns:
        Parsed datetime
    """
    if isinstance(timestamp_value, str):
        # ISO 8601 format
        return datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
    elif isinstance(timestamp_value, (int, float)):
        # Unix epoch
        return datetime.fromtimestamp(timestamp_value)
    else:
        raise ValueError(f"Invalid timestamp type: {type(timestamp_value)}")


@dataclass
class TextLabel:
    """Text label with timestamp and content, overlaid on its closest photo."""
    timestamp: datetime
    text: str

    @classmethod
    def from_dict(cls, data: dict) -> 'TextLabel':
        """
        Create TextLabel from configuration dictionary.

        Args:
            data: Dictionary with 'timestamp' and 'text' fields

        Returns:
            TextLabel instance
        """
        return cls(timestamp=_parse_timestamp(data['timestamp']), text=data['text'])


@dataclass
class TitleLabel:
    """Title label with timestamp and content; consumes its own page slot."""
    timestamp: datetime
    title: str

    @property
    def orientation(self) -> str:
        """Titles always present as portrait orientation for layout template matching."""
        return 'portrait'

    @classmethod
    def from_dict(cls, data: dict) -> 'TitleLabel':
        """
        Create TitleLabel from configuration dictionary.

        Args:
            data: Dictionary with 'timestamp' and 'title' fields

        Returns:
            TitleLabel instance
        """
        return cls(timestamp=_parse_timestamp(data['timestamp']), title=data['title'])


@dataclass
class TextSegment:
    """Text segment with formatting style."""
    text: str
    bold: bool = False
    italic: bool = False
    heading_level: int = 0  # 0 = normal, 1-3 = heading levels
    
    @property
    def font_size_multiplier(self) -> float:
        """Get font size multiplier based on heading level."""
        if self.heading_level == 1:
            return 1.5
        elif self.heading_level == 2:
            return 1.3
        elif self.heading_level == 3:
            return 1.2
        else:
            return 1.0


def parse_markdown_line(line: str) -> tuple[List[TextSegment], int]:
    """
    Parse a single line of text with markdown formatting.
    
    Args:
        line: Line of text with markdown markers
        
    Returns:
        Tuple of (list of TextSegment objects, heading_level)
    """
    # Check for heading markers at start of line
    heading_level = 0
    if line.startswith('### '):
        heading_level = 3
        line = line[4:]
    elif line.startswith('## '):
        heading_level = 2
        line = line[3:]
    elif line.startswith('# '):
        heading_level = 1
        line = line[2:]
    
    # Parse inline formatting (bold and italic)
    segments = []
    
    # Pattern to match **bold**, *italic*, _italic_, and ***bold+italic***
    # Process in order: bold+italic first, then bold, then italic
    pattern = r'(\*\*\*[^*]+\*\*\*|\*\*[^*]+\*\*|\*[^*]+\*|_[^_]+_)'
    
    last_end = 0
    for match in re.finditer(pattern, line):
        # Add plain text before this match
        if match.start() > last_end:
            plain_text = line[last_end:match.start()]
            if plain_text:
                segments.append(TextSegment(
                    text=plain_text,
                    bold=False,
                    italic=False,
                    heading_level=heading_level
                ))
        
        # Parse the matched formatting
        matched_text = match.group(0)
        
        if matched_text.startswith('***') and matched_text.endswith('***'):
            # Bold + italic
            text = matched_text[3:-3]
            segments.append(TextSegment(
                text=text,
                bold=True,
                italic=True,
                heading_level=heading_level
            ))
        elif matched_text.startswith('**') and matched_text.endswith('**'):
            # Bold only
            text = matched_text[2:-2]
            segments.append(TextSegment(
                text=text,
                bold=True,
                italic=False,
                heading_level=heading_level
            ))
        elif matched_text.startswith('*') and matched_text.endswith('*'):
            # Italic only
            text = matched_text[1:-1]
            segments.append(TextSegment(
                text=text,
                bold=False,
                italic=True,
                heading_level=heading_level
            ))
        elif matched_text.startswith('_') and matched_text.endswith('_'):
            # Italic only (underscore form)
            text = matched_text[1:-1]
            segments.append(TextSegment(
                text=text,
                bold=False,
                italic=True,
                heading_level=heading_level
            ))

        last_end = match.end()
    
    # Add remaining plain text
    if last_end < len(line):
        plain_text = line[last_end:]
        if plain_text:
            segments.append(TextSegment(
                text=plain_text,
                bold=False,
                italic=False,
                heading_level=heading_level
            ))
    
    # Handle graceful degradation - if no segments, return plain line
    if not segments:
        segments.append(TextSegment(
            text=line,
            bold=False,
            italic=False,
            heading_level=heading_level
        ))
    
    return segments, heading_level


def parse_markdown_text(text: str) -> List[tuple[List[TextSegment], int]]:
    """
    Parse multi-line text with markdown formatting.

    Leading and trailing blank lines are trimmed before parsing - these are
    typically formatting artifacts (e.g. the trailing newline YAML's `|`
    block scalar always keeps) rather than intentional spacing. Blank lines
    between non-blank lines are preserved.

    Args:
        text: Text content with markdown markers

    Returns:
        List of tuples (segments, heading_level) for each line
    """
    lines = text.split('\n')

    start = 0
    while start < len(lines) and lines[start] == '':
        start += 1
    end = len(lines)
    while end > start and lines[end - 1] == '':
        end -= 1
    lines = lines[start:end]

    parsed_lines = []

    for line in lines:
        segments, heading_level = parse_markdown_line(line)
        parsed_lines.append((segments, heading_level))

    return parsed_lines


def find_closest_photo(text_label: TextLabel, photos: List) -> Optional[any]:
    """
    Find the photo with timestamp closest to the text label.
    
    Args:
        text_label: TextLabel to match
        photos: List of PhotoMetadata objects with sort_date property
        
    Returns:
        Closest PhotoMetadata object, or None if no photos
    """
    if not photos:
        return None
    
    # Find photo with minimum time difference
    closest_photo = None
    min_diff = None
    
    for photo in photos:
        # Use photo.sort_date which returns the best available date
        time_diff = abs((photo.sort_date - text_label.timestamp).total_seconds())
        
        if min_diff is None or time_diff < min_diff:
            min_diff = time_diff
            closest_photo = photo
        elif time_diff == min_diff:
            # Deterministic tiebreaker: prefer earlier photo
            if photo.sort_date < closest_photo.sort_date:
                closest_photo = photo
    
    return closest_photo


def associate_text_labels_with_photos(
    text_labels: List[Dict],
    photos: List
) -> List[tuple]:
    """
    Associate text labels with photos based on timestamps.
    
    Args:
        text_labels: List of text label dictionaries from configuration
        photos: List of PhotoMetadata objects
        
    Returns:
        List of tuples (PhotoMetadata, TextLabel or None)
    """
    # Parse text labels
    parsed_labels = []
    for label_data in text_labels:
        try:
            label = TextLabel.from_dict(label_data)
            parsed_labels.append(label)
        except (ValueError, KeyError) as e:
            # Skip invalid labels (already validated in config)
            continue
    
    if not parsed_labels:
        # No text labels - return photos with None labels
        return [(photo, None) for photo in photos]
    
    # Build mapping: photo index -> text label
    # For each text label, find the closest photo
    photo_idx_to_label = {}
    
    for label in parsed_labels:
        # Find the closest photo for this label
        closest_photo = find_closest_photo(label, photos)
        if closest_photo:
            # Find the index of this photo
            closest_idx = photos.index(closest_photo)
            
            # Associate this label with the closest photo
            # If the photo already has a label, keep the one with closer timestamp
            if closest_idx in photo_idx_to_label:
                existing_label = photo_idx_to_label[closest_idx]
                existing_diff = abs((closest_photo.sort_date - existing_label.timestamp).total_seconds())
                new_diff = abs((closest_photo.sort_date - label.timestamp).total_seconds())
                if new_diff < existing_diff:
                    photo_idx_to_label[closest_idx] = label
            else:
                photo_idx_to_label[closest_idx] = label
    
    # Build result list in the same order as photos
    associations = []
    for idx, photo in enumerate(photos):
        label = photo_idx_to_label.get(idx, None)
        associations.append((photo, label))

    return associations


def parse_title_labels(text_labels: List[Dict]) -> List[TitleLabel]:
    """
    Parse title entries from configuration, skipping any without a 'title' field.

    Args:
        text_labels: List of text label dictionaries from configuration

    Returns:
        List of TitleLabel instances (invalid entries skipped; already validated in config)
    """
    titles = []
    for label_data in text_labels:
        if 'title' not in label_data:
            continue
        try:
            titles.append(TitleLabel.from_dict(label_data))
        except (ValueError, KeyError):
            continue
    return titles


def merge_titles_with_photos(titles: List[TitleLabel], photos: List) -> List:
    """
    Merge title items chronologically into the photo sequence, producing the
    final ordered sequence of page items (photos and titles combined).

    Each title is inserted immediately before the first photo whose sort_date
    is greater than or equal to the title's timestamp (appended at the end if
    no such photo exists). Comparing with >= rather than > is what makes a
    title win an exact timestamp tie with a photo: the tied photo is itself
    the first one satisfying the condition, so the title lands right before it.

    Args:
        titles: TitleLabel items to merge in, any order
        photos: PhotoMetadata items in their final display order

    Returns:
        Merged list of photos and titles in final page order
    """
    sorted_titles = sorted(titles, key=lambda t: t.timestamp)

    merged = []
    title_idx = 0

    for photo in photos:
        while title_idx < len(sorted_titles) and sorted_titles[title_idx].timestamp <= photo.sort_date:
            merged.append(sorted_titles[title_idx])
            title_idx += 1
        merged.append(photo)

    # Any remaining titles are later than every photo
    merged.extend(sorted_titles[title_idx:])

    return merged

