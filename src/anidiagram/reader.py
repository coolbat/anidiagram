"""Optional reading surfaces; canonical SVG and motion stay independent."""

from html import escape


def evidence_markup(scene, locale):
    title = "源码引用已核验" if locale == "zh-CN" else "Verified source references"
    note = ("核验范围：固定提交中的文件和行号；架构含义仍需评审。" if locale == "zh-CN" else
            "Verification covers files and lines at the pinned commit; architectural claims still need review.")
    rows = []
    for source in scene.source_evidence["sources"]:
        subjects = [key for key, refs in scene.source_evidence["subjects"].items() if source["id"] in refs]
        label = source["title"] + " · " + source["repository"]["revision"][:7]
        rows.append(f'<li><a href="{escape(source["href"], quote=True)}" target="_blank" rel="noopener noreferrer">{escape(label)}</a> {escape(", ".join(subjects))}</li>')
    return f'<details id="source-evidence"><summary>{title}</summary><p>{note}</p><ul>{"".join(rows)}</ul></details>\n'
