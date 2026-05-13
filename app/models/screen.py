import enum

from sqlalchemy import Enum as SAEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class ScreenType(str, enum.Enum):
    STANDARD = "STANDARD"
    IMAX = "IMAX"
    THREE_D = "3D"
    FOUR_D = "4D"
    DOLBY = "DOLBY"


class Screen(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "screens"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    screen_type: Mapped[ScreenType] = mapped_column(
        SAEnum(ScreenType), nullable=False, default=ScreenType.STANDARD
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    seats: Mapped[list["Seat"]] = relationship("Seat", back_populates="screen")
    showtimes: Mapped[list["Showtime"]] = relationship("Showtime", back_populates="screen")
