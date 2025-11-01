import csv
import json
from typing import Dict, List, Optional, Tuple

# ---------------------- Node class ----------------------
class Node:
    """
    - student_id: mã sinh viên (string)
    - year_of_study: năm học (int)
    - gpa: điểm GPA (float)
    - next: tham chiếu tới node tiếp theo (None nếu là node cuối)
    """
    def __init__(self, student_id: str, year_of_study: int, gpa: float):
        self.student_id = student_id
        self.year_of_study = year_of_study
        self.gpa = float(gpa)
        self.next: Optional['Node'] = None

    def __repr__(self):
        return f"Node({self.student_id}, {self.year_of_study}, {self.gpa})"


# ---------------------- Khởi tạo mapping head->None ----------------------
def init_heads(head_keys: List[float]) -> Dict[float, Optional[Node]]:
    """
    Khởi tạo dict chứa head tới None ban đầu (chưa có danh sách).
    Ví dụ: {1.22: None, 2.03: None, ...}
    """
    return {h: None for h in head_keys}


# ---------------------- add_tail-----------------------
def add_tail(mapping: Dict[float, Optional[Node]], head_key: float, node_to_add: Node) -> None:
    """
    Thêm node_to_add vào cuối linked list của mapping[head_key].
    - Nếu mapping[head_key] là None: node_to_add sẽ là node đầu.
    - Ngược lại: duyệt tới cuối rồi nối.
    """
    if mapping[head_key] is None:
        mapping[head_key] = node_to_add
    else:
        cur = mapping[head_key]
        while cur.next:
            cur = cur.next
        cur.next = node_to_add


# ---------------------- Tìm GPA gần nhất trong bucket / file ----------------------
def find_nearest_head(head_value: float, gpas_in_file: List[float], sorted_gpas: List[float]) -> Optional[float]:
    """
    Tìm giá trị GPA thực tế gần nhất để dùng làm head cho bucket head_value:
    1) Nếu có GPA trong đoạn [head_value, head_value+0.99] -> trả GPA nhỏ nhất trong khoảng đó.
    2) Nếu không có -> tìm GPA lớn hơn gần nhất trong toàn file (theo sorted_gpas).
    3) Nếu không tìm được -> trả None.
    """
    lower = head_value
    upper = head_value + 0.99

    # Candidate trong bucket
    candidates = [g for g in gpas_in_file if lower <= g <= upper]
    if candidates:
        return min(candidates)

    # Fallback: tìm gpa > upper (giá trị lớn hơn gần nhất)
    for gpa in sorted_gpas:
        if gpa > upper:
            return gpa

    return None


# ---------------------- Đọc CSV, xác định head thực và build buckets (lưu nodes) ----------------------
def build_graph_from_csv(csv_file: str, max_rows: Optional[int] = None
                         ) -> Tuple[Dict[float, Optional[Node]], List[float], Dict[float, Optional[Node]]]:
    """
    Quy trình:
    1. Đọc toàn bộ (hoặc max_rows) sinh viên từ CSV thành danh sách students (để tôn trọng thứ tự file).
    2. Từ danh sách đó, lấy tất cả GPA và sorted_gpas.
    3. Với mỗi base head [0.0,1.0,2.0,3.0,4.0], tìm giá trị head_resolved bằng find_nearest_head.
       - Nếu không tìm được (trường hợp 4.0 không có) thì giữ None cho 4.0.
    4. Tạo mapping = init_heads(heads_resolved) (keys là các head thực có giá trị).
    5. Duyệt lại danh sách students theo thứ tự file:
       - Tìm head bucket h mà student thuộc về (h <= gpa <= h+0.99)
       - Tạo Node và add_tail(mapping, h, node)
       - Đồng thời, nếu head_primary[h] chưa có và node.gpa == h (hoặc node.gpa == head_resolved), gán head_primary[h] = node
    Trả về:
       - mapping: head_resolved -> linked list các node thuộc bucket
       - heads_resolved: danh sách các head thực đã được resolve (loại None trừ 4.0 đặc biệt)
       - head_primary: head_resolved -> node được chọn làm head (thông tin student cho head)
    """
    # 1) base heads cố định
    base_heads = [0.0, 1.0, 2.0, 3.0, 4.0]

    # 2) đọc file CSV vào danh sách students
    students: List[dict] = []
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

    # 3) lấy danh sách GPA và sorted
    gpas = [s['gpa'] for s in students]
    sorted_gpas = sorted(gpas)

    # 4) resolve head values (có thể là giá trị gpa thực tế)
    heads_resolved: List[Optional[float]] = []
    for hd in base_heads:
        nearest = find_nearest_head(hd, gpas, sorted_gpas)
        # Với 4.0: nếu nearest là None thì ta vẫn muốn giữ 4.0 như key xuất file nhưng không gán node
        if hd == 4.0 and nearest is None:
            heads_resolved.append(4.0)  # giữ 4.0 như key (sẽ có mapping[4.0]=None)
        else:
            if nearest is None:
                # nếu không tìm được và không phải 4.0 -> skip (hiếm xảy ra)
                continue
            heads_resolved.append(nearest)

    # loại bỏ duplicate (vì nearest có thể tạo các giá trị giống nhau); giữ thứ tự xuất hiện của heads_resolved
    unique_heads = []
    for h in heads_resolved:
        if h not in unique_heads:
            unique_heads.append(h)
    heads_resolved = sorted(unique_heads)

    # 5) init mapping và head_primary
    mapping: Dict[float, Optional[Node]] = init_heads(heads_resolved)
    head_primary: Dict[float, Optional[Node]] = {h: None for h in heads_resolved}

    # 6) Duyệt students theo thứ tự file và add vào mapping
    for stu in students:
        stu_gpa = stu["gpa"]
        # tìm head bucket mà student thuộc về: head <= gpa <= head+0.99
        assigned = False
        for h in heads_resolved:
            if h <= stu_gpa <= h + 0.99:
                node = Node(stu["id"], stu["year"], stu_gpa)
                # nếu head_primary chưa có node và node chính là candidate head (gpa == h), gán
                if head_primary[h] is None and abs(node.gpa - h) < 1e-9:
                    head_primary[h] = node
                add_tail(mapping, h, node)
                assigned = True
                break

    # 7) Sau khi thêm tất cả node, nếu head_primary vẫn None nhưng mapping có node,
    #    chọn node đầu tiên trong mapping[head] làm head_primary
    for h in heads_resolved:
        if head_primary.get(h) is None and mapping.get(h) is not None:
            head_primary[h] = mapping[h]  # node đầu tiên trong linked list

    # Kết thúc: trả về mapping, heads_resolved (sorted), head_primary
    return mapping, heads_resolved, head_primary

# ---------------------- Xuất ra JSON ----------------------
def export_to_json(mapping: Dict[float, Optional[Node]],
                   heads: List[float],
                   head_primary: Dict[float, Optional[Node]],
                   json_path: str) -> None:
    """
    Xuất ra file JSON theo format:
    - Key: có một vài dòng trống trước để dễ đọc (user muốn vậy)
    - Value: một chuỗi (một dòng) theo mẫu:
        "(head_gpa, head_student_id, head_year) -> (node1_gpa, id, year)|w1 -> ... -> (next_head_gpa, next_id, next_year)|wN"
      Nếu head_primary[h] không tồn tại: in "(head, noval_HEAD, noval_HEAD)".
      Nếu next head không có thông tin sinh viên: in "(next_head, noval_nHEAD, noval_nHEAD)|nowei_nHead".
    Lưu ý: không in chữ 'next head', chỉ in tuple đầy đủ.
    """
    json_dict: Dict[str, str] = {}

    sorted_heads = sorted(heads)  # đảm bảo thứ tự tăng dần

    for i, head in enumerate(sorted_heads):
        parts: List[str] = []

        # HEAD: in thông tin full nếu head_primary có node, ngược lại in noval_HEAD
        primary = head_primary.get(head)
        if primary:
            parts.append(f"({primary.gpa}, {primary.student_id}, {primary.year_of_study})")
        else:
            # nếu head là 4.0 và không có node, in placeholder (theo yêu cầu)
            parts.append(f"({head}, noval_HEAD, noval_HEAD)")

        # Các node trong bucket (theo linked list mapping[head])
        cur = mapping.get(head)
        # Nếu head_primary tồn tại và nó chính là node đầu trong mapping, ta phải bỏ qua khi lặp
        # nhưng hiện mapping[head] có node đầu = head_primary (nếu gán), nên ta cần đảm bảo không in double.
        # Do mình gán head_primary[h] = mapping[h] nếu head_primary rỗng, nên in trực tiếp các node sau head_primary
        # để tránh double print, ta sẽ bắt đầu từ mapping[head] và in tất cả node; nếu prviary matches first node,
        # sẽ dẫn đến hai lần in; vì vậy cần logic: nếu primary exists and primary == mapping[head], skip first when printing nodes.

        first_node = mapping.get(head)
        cur = first_node
        skip_first = False
        if primary and first_node and abs(primary.gpa - first_node.gpa) < 1e-9 and primary.student_id == first_node.student_id:
            # nếu primary là chính node đầu trong linked list -> khi in nodes ta sẽ bắt đầu từ first_node.next
            skip_first = True
            cur = first_node.next

        # In các node còn lại
        while cur:
            diff = round(cur.gpa - head, 2)
            parts.append(f"({cur.gpa}, {cur.student_id}, {cur.year_of_study})|{diff}")
            cur = cur.next

        # In thông tin nextHead
        if i < len(sorted_heads) - 1:
            next_h = sorted_heads[i + 1]
            next_primary = head_primary.get(next_h)
            if next_primary:
                weight_to_next = round(next_primary.gpa - head, 2)
                parts.append(f"({next_primary.gpa}, {next_primary.student_id}, {next_primary.year_of_study})|{weight_to_next}")
            else:
                # Khi không có GPA 4.0 thì in ra dòng này ở nextHEAD của 3.0
                parts.append(f"({next_h}, noval_nHEAD, noval_nHEAD)|nowei_nHead")
        else:
            # head cuối cùng (không có next) -> pass
            pass

        # Tên head
        json_dict[f"\n\n\n{head}"] = " -> ".join(parts)

    # In 4.0 là noval nếu không có sinh viên có giá trị này
    if 4.0 not in sorted_heads:
        json_dict[f"\n\n\n4.0"] = f"(4.0, noval_HEAD, noval_HEAD)"

    # Ghi file JSON
    with open(json_path, 'w', encoding='utf-8') as jf:
        json.dump(json_dict, jf, indent=4, ensure_ascii=False)


# ---------------------- main ----------------------
if __name__ == "__main__":
    # Đường dẫn file CSV
    csv_path = "Cleaned_Australian_Student_PerformanceData (ASPD24).csv"
    json_out = "output.json"

    # Đọc và xây graph (None = đọc hết file)
    mapping, heads, head_primary = build_graph_from_csv(csv_path, max_rows=50)

    # Xuất file JSON theo format yêu cầu
    export_to_json(mapping, heads, head_primary, json_out)

    print("Đã ghi file JSON thành công:", json_out)
