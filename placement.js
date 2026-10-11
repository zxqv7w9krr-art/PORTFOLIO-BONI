const seatMap = document.querySelector("#seat-map");
const positions = [];

for (let col = 4; col < 12; col += 1) positions.push([0, col]);
for (let col = 4; col < 11; col += 1) positions.push([1, col]);
for (let col = 7; col < 10; col += 1) positions.push([2, col]);
for (let row = 2; row < 8; row += 1) positions.push([row, 1]);
for (let row = 3; row < 7; row += 1) positions.push([row, 2]);
for (let row = 3; row < 6; row += 1) positions.push([row, 3]);
for (let row = 4; row < 6; row += 1) positions.push([row, 4]);
for (let row = 2; row < 8; row += 1) positions.push([row, 14]);
for (let row = 3; row < 7; row += 1) positions.push([row, 13]);
for (let row = 3; row < 6; row += 1) positions.push([row, 12]);
for (let row = 4; row < 6; row += 1) positions.push([row, 11]);

positions.forEach(([row, col], index) => {
  const seat = document.createElement("span");
  seat.className = "map-seat";
  seat.textContent = String(index + 1).padStart(2, "0");
  seat.style.gridArea = `${row + 1} / ${col + 1}`;
  seat.setAttribute("aria-label", `Place ${index + 1}`);
  seatMap.append(seat);
});
