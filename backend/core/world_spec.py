from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator


Wall = Literal["north", "south", "east", "west"]


class Plot(BaseModel):
    width: float = Field(default=100.0, gt=0)
    depth: float = Field(default=100.0, gt=0)
    groundColor: str = "#5a7c3a"


class Entrance(BaseModel):
    wall: Wall
    offset: float = Field(ge=0)
    width: float = Field(default=1.6, gt=0)
    height: float = Field(default=2.2, gt=0)


class Site(BaseModel):
    plot: Plot = Field(default_factory=Plot)
    buildingFootprint: list[float]
    buildingAnchor: list[float]
    entrance: Entrance


class Door(BaseModel):
    wall: Wall
    offset: float = Field(ge=0)
    width: float = Field(gt=0)


class Window(BaseModel):
    wall: Wall
    offset: float = Field(ge=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    sill: float = Field(ge=0)


class Room(BaseModel):
    id: str
    type: str
    x: float
    y: float
    width: float = Field(gt=0)
    depth: float = Field(gt=0)
    doors: list[Door] = Field(default_factory=list)
    windows: list[Window] = Field(default_factory=list)


class Stairs(BaseModel):
    id: str
    x: float
    y: float
    width: float = Field(gt=0)
    depth: float = Field(gt=0)
    direction: Wall
    toLevel: int


class Floor(BaseModel):
    level: int
    ceilingHeight: float = Field(gt=0)
    rooms: list[Room]
    stairs: list[Stairs] = Field(default_factory=list)


class Blueprint(BaseModel):
    gridSize: float = 0.5
    floors: list[Floor]

    @model_validator(mode="after")
    def _check_grid_alignment(self) -> "Blueprint":
        g = self.gridSize
        eps = 1e-6
        def aligned(v: float) -> bool:
            return abs((v / g) - round(v / g)) < eps
        for fl in self.floors:
            for r in fl.rooms:
                for v in (r.x, r.y, r.width, r.depth):
                    if not aligned(v):
                        raise ValueError(f"room {r.id} value {v} not aligned to grid {g}")
        return self


class Intent(BaseModel):
    buildingType: str
    style: str
    floors: int = Field(ge=1, le=4)
    vibe: list[str] = Field(default_factory=list)
    sizeHint: str = "medium"


class GeometryPrimitive(BaseModel):
    type: Literal["floor", "wall", "ceiling", "stair"]
    roomId: Optional[str] = None
    wall: Optional[Wall] = None
    position: list[float]
    size: list[float]
    rotation: float = 0.0
    holes: list[dict] = Field(default_factory=list)


class Geometry(BaseModel):
    primitives: list[GeometryPrimitive] = Field(default_factory=list)


class Light(BaseModel):
    type: Literal["ceiling", "lamp", "ambient"]
    position: list[float]
    color: str = "#ffffff"
    intensity: float = 1.0


class LightingByRoom(BaseModel):
    byRoom: dict[str, list[Light]] = Field(default_factory=dict)


class RoomMaterial(BaseModel):
    wall: str
    floor: str
    ceiling: str


class MaterialsByRoom(BaseModel):
    byRoom: dict[str, RoomMaterial] = Field(default_factory=dict)


class FurnitureItem(BaseModel):
    id: str
    roomId: str
    type: str
    subtype: Optional[str] = None
    position: list[float]
    rotation: float = 0.0
    size: list[float]
    selectedProductId: Optional[str] = None
    alternates: list[str] = Field(default_factory=list)
    tint: Optional[str] = None


class Product(BaseModel):
    name: str
    price: Optional[float] = None
    imageUrl: Optional[str] = None
    vendor: Optional[str] = None
    url: Optional[str] = None
    fitsTypes: list[str] = Field(default_factory=list)


class Navigation(BaseModel):
    spawnPoint: list[float]
    walkableMeshIds: list[str] = Field(default_factory=list)
    stairColliders: list[str] = Field(default_factory=list)


class Cost(BaseModel):
    total: float = 0
    byRoom: dict[str, float] = Field(default_factory=dict)


Lighting = LightingByRoom
Materials = MaterialsByRoom


class WorldSpec(BaseModel):
    worldId: str
    prompt: str
    intent: Optional[Intent] = None
    blueprint: Optional[Blueprint] = None
    geometry: Optional[Geometry] = None
    lighting: Optional[Lighting] = None
    materials: Optional[Materials] = None
    furniture: list[FurnitureItem] = Field(default_factory=list)
    products: dict[str, Product] = Field(default_factory=dict)
    navigation: Optional[Navigation] = None
    cost: Optional[Cost] = None
