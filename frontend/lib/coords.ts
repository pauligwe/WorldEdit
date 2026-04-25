export function bpToScene(x: number, y: number, levelY = 0): [number, number, number] {
  return [x, levelY, -y];
}

export function levelYOffset(level: number, ceilingHeight = 3.0): number {
  return level * ceilingHeight;
}
