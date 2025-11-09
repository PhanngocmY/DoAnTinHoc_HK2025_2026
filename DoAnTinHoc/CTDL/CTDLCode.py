import csv
import json
import heapq

# ---------------------- Node class ----------------------
class Node:
    def __init__(self, student_id, year_of_study, gpa):
        self.student_id = student_id
        self.year_of_study = year_of_study
        self.gpa = float(gpa)
        self.next = None

    def __repr__(self):
        return f"Node({self.student_id}, {self.year_of_study}, {self.gpa})"


# ---------------------- Khởi tạo mapping head->None ----------------------
def init_heads(head_keys):
    return {h: None for h in head_keys}


# ---------------------- add_tail-----------------------
def add_tail(mapping, head_key, node_to_add):
    if mapping[head_key] is None:
        mapping[head_key] = node_to_add
    else:
        cur = mapping[head_key]
        while cur.next:
            cur = cur.next
        cur.next = node_to_add


# ---------------------- Tìm GPA gần nhất trong khoảng / file ----------------------
def find_nearest_head(head_value, gpas_in_file, sorted_gpas):
    lower = head_value
    upper = head_value + 0.99

    # Candidate trong khoảng
    candidates = [g for g in gpas_in_file if lower <= g <= upper]
    if candidates:
        return min(candidates)

    # Fallback: tìm gpa > upper (giá trị lớn hơn gần nhất)
    for gpa in sorted_gpas:
        if gpa > upper:
            return gpa

    return None


# ---------------------- Đọc CSV, xác định head thực và build khoảng ----------------------
def build_graph_from_csv(csv_file, max_rows=None):
    base_heads = [0.0, 1.0, 2.0, 3.0, 4.0]
    students = []

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if max_rows is not None and i >= max_rows:
                break
            students.append({
                "id": row['Student ID'],
                "year": int(row['Year of Study']),
                "gpa": float(row['GPA'])
            })

    gpas = [s['gpa'] for s in students]
    sorted_gpas = sorted(gpas)

    heads_resolved = []
    for hd in base_heads:
        nearest = find_nearest_head(hd, gpas, sorted_gpas)
        if hd == 4.0 and nearest is None:
            heads_resolved.append(4.0)
        elif nearest is not None:
            heads_resolved.append(nearest)

    unique_heads = sorted(set(heads_resolved))
    mapping = init_heads(unique_heads)
    head_primary = {h: None for h in unique_heads}

    for stu in students:
        stu_gpa = stu["gpa"]
        for h in unique_heads:
            if h <= stu_gpa <= h + 0.99:
                node = Node(stu["id"], stu["year"], stu_gpa)
                if head_primary[h] is None and abs(node.gpa - h) < 1e-9:
                    head_primary[h] = node
                add_tail(mapping, h, node)
                break

    for h in unique_heads:
        if head_primary[h] is None and mapping[h] is not None:
            head_primary[h] = mapping[h]

    return mapping, unique_heads, head_primary


# ---------------------- Xuất ra JSON ----------------------
def export_to_json(mapping, heads, head_primary, json_path):
    json_dict = {}
    sorted_heads = sorted(heads)

    for i, head in enumerate(sorted_heads):
        parts = []
        primary = head_primary.get(head)
        if primary:
            parts.append(f"({primary.gpa}, {primary.student_id}, {primary.year_of_study})")
        else:
            parts.append(f"({head}, noval_HEAD, noval_HEAD)")

        cur = mapping.get(head)
        if primary and cur and abs(primary.gpa - cur.gpa) < 1e-9 and primary.student_id == cur.student_id:
            cur = cur.next

        while cur:
            diff = round(cur.gpa - head, 2)
            parts.append(f"({cur.gpa}, {cur.student_id}, {cur.year_of_study})|{diff}")
            cur = cur.next

        if i < len(sorted_heads) - 1:
            next_h = sorted_heads[i + 1]
            next_primary = head_primary.get(next_h)
            if next_primary:
                weight_to_next = round(next_primary.gpa - head, 2)
                parts.append(f"({next_primary.gpa}, {next_primary.student_id}, {next_primary.year_of_study})|{weight_to_next}")
        json_dict[str(head)] = " -> ".join(parts)

    with open(json_path, 'w', encoding='utf-8') as jf:
        json.dump(json_dict, jf, indent=4, ensure_ascii=False)


# ---------------------- Tạo graph kề từ heads ----------------------
def convert_to_graph(mapping):
    """
    Chuyển cấu trúc danh sách liên kết thành đồ thị (dict)
    Mỗi head và các node nối tiếp nhau sẽ là các đỉnh có cạnh (gpa -> next.gpa)
    """
    graph = {}
    for head, node in mapping.items():
        graph[head] = []
        cur = node
        while cur and cur.next:
            w = round(abs(cur.next.gpa - cur.gpa), 2)
            graph.setdefault(cur.gpa, []).append((cur.next.gpa, w))
            graph.setdefault(cur.next.gpa, [])
            cur = cur.next
    return graph

# ---------------------- BFS ----------------------
def bfs(graph, start):
    visited, queue = set(), [start]
    order = []
    while queue:
        v = queue.pop(0)
        if v not in visited:
            visited.add(v)
            order.append(v)
            for neighbor, _ in graph[v]:
                if neighbor not in visited:
                    queue.append(neighbor)
    return order


# ---------------------- DFS ----------------------
def dfs(graph, start, visited=None, order=None):
    if visited is None:
        visited, order = set(), []
    visited.add(start)
    order.append(start)
    for neighbor, _ in graph[start]:
        if neighbor not in visited:
            dfs(graph, neighbor, visited, order)
    return order


# ---------------------- Prim ----------------------
def prim(graph, start):
    visited = set([start])
    edges = [
        (w, start, to) for to, w in graph[start]
    ]
    heapq.heapify(edges)
    mst = []
    while edges:
        w, frm, to = heapq.heappop(edges)
        if to not in visited:
            visited.add(to)
            mst.append((frm, to, w))
            for nxt, nw in graph[to]:
                if nxt not in visited:
                    heapq.heappush(edges, (nw, to, nxt))
    return mst


# ---------------------- Kruskal ----------------------
def kruskal(graph):
    parent = {}
    def find(u):
        if parent[u] != u:
            parent[u] = find(parent[u])
        return parent[u]
    def union(u, v):
        ru, rv = find(u), find(v)
        parent[rv] = ru

    for v in graph:
        parent[v] = v

    edges = []
    for u in graph:
        for v, w in graph[u]:
            if u < v:
                edges.append((w, u, v))
    edges.sort()

    mst = []
    for w, u, v in edges:
        if find(u) != find(v):
            union(u, v)
            mst.append((u, v, w))
    return mst


# ---------------------- Dijkstra ----------------------
def dijkstra(graph, start):
    dist = {v: float('inf') for v in graph}
    dist[start] = 0
    pq = [(0, start)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v, w in graph[u]:
            if dist[v] > d + w:
                dist[v] = d + w
                heapq.heappush(pq, (dist[v], v))
    return dist


# ---------------------- Floyd-Warshall ----------------------
def floyd(graph):
    vertices = list(graph.keys())
    n = len(vertices)
    dist = {u: {v: float('inf') for v in vertices} for u in vertices}
    for u in vertices:
        dist[u][u] = 0
        for v, w in graph[u]:
            dist[u][v] = w

    for k in vertices:
        for i in vertices:
            for j in vertices:
                if dist[i][j] > dist[i][k] + dist[k][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
    return dist


# ---------------------- Topo sort (DAG) ----------------------
def topo_sort(graph):
    indeg = {u: 0 for u in graph}
    for u in graph:
        for v, _ in graph[u]:
            indeg[v] += 1
    queue = [u for u in graph if indeg[u] == 0]
    order = []
    while queue:
        u = queue.pop(0)
        order.append(u)
        for v, _ in graph[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)
    return order


# ---------------------- MAIN TEST ----------------------
if __name__ == "__main__":
    if __name__ == "__main__":
        csv_path = "Australian_Student_PerformanceData (ASPD24).csv"
        json_out = "Output.json"

        mapping, heads, head_primary = build_graph_from_csv(csv_path)
        export_to_json(mapping, heads, head_primary, json_out)

        # Dùng cấu trúc thật từ dataset
        graph = convert_to_graph(mapping)

        print("BFS:", bfs(graph, heads[0]))
        print("DFS:", dfs(graph, heads[0]))
        print("Prim:", prim(graph, heads[0]))
        print("Kruskal:", kruskal(graph))
        print("Dijkstra:", dijkstra(graph, heads[0]))
        print("Floyd:", floyd(graph))
        print("Topo:", topo_sort(graph))

