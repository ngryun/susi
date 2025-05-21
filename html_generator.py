from data_processor import compute_additional_stats, compute_stats, NumpyEncoder # data_processor 모듈이 있다고 가정합니다.
from pathlib import Path
import json
# Assuming data_processor.py contains these (as per original imports)
# from data_processor import compute_additional_stats, compute_stats, NumpyEncoder
import pandas as pd

# Dummy NumpyEncoder for standalone execution if needed
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        import numpy as np
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

# Dummy compute_additional_stats for standalone execution if needed
def compute_additional_stats(data, grade_type):
    # Replace with actual implementation
    # This is a placeholder
    if data.empty:
        return {}
    stats = {}
    for result_key in ["합격", "충원합격", "불합격"]:
        result_data = data[data["result"] == result_key][grade_type].dropna()
        if not result_data.empty:
            stats[result_key] = {
                'count': len(result_data),
                'mean': result_data.mean() if len(result_data) > 0 else 'N/A',
                'std': result_data.std() if len(result_data) > 1 else 'N/A',
                'median': result_data.median() if len(result_data) > 0 else 'N/A',
                'max': result_data.max() if len(result_data) > 0 else 'N/A',
                'min': result_data.min() if len(result_data) > 0 else 'N/A',
                'q1': result_data.quantile(0.25) if len(result_data) > 0 else 'N/A',
                'q3': result_data.quantile(0.75) if len(result_data) > 0 else 'N/A',
            }
        else:
            stats[result_key] = {'count': 0}
    return stats

# create_additional_stats_html function from the user (assumed to be correct)
def create_additional_stats_html(stats, grade_type, result_order=["합격", "충원합격", "불합격"]):
    """
    추가 통계 정보를 HTML 테이블로 형식화.
    모든 등급 타입에 대해 동일한 형식 사용 (변동계수 열 제외)
    result_order: 결과를 표시할 순서
    """
    if not stats:
        return "<div class='no-stats'>통계 데이터가 없습니다.</div>"

    html_output = f"""
    <div class="stats-detail-title">{grade_type} 상세 통계</div>
    <table class="stats-table">
        <thead>
            <tr>
    """

    headers = ["결과", "데이터 수", "평균", "표준편차", "중앙값", "최댓값", "최솟값", "Q1-Q3 범위"]
    for header in headers:
        html_output += f"<th>{header}</th>"
    html_output += """
        </tr>
    </thead>
    <tbody>
    """

    for result_key_name in result_order:
        # Check if the result_key_name exists and has data
        if result_key_name not in stats or not isinstance(stats[result_key_name], dict) or stats[result_key_name].get('count', 0) == 0:
            # If key doesn't exist or count is 0, display '데이터 없음'
            num_cols = len(headers)
            html_output += f"""<tr><td>{result_key_name}</td><td colspan='{num_cols-1}' style='text-align:center;'>데이터 없음</td></tr>"""
            continue

        result_stats_data = stats[result_key_name]
        color_class = ""
        if result_key_name == "합격": color_class = "pass-row"
        elif result_key_name == "불합격": color_class = "fail-row"
        elif result_key_name == "충원합격": color_class = "waitlist-row"

        mean_val = f"{result_stats_data.get('mean', 'N/A'):.2f}" if isinstance(result_stats_data.get('mean'), (int, float)) else "N/A"
        std_val = f"{result_stats_data.get('std', 'N/A'):.2f}" if isinstance(result_stats_data.get('std'), (int, float)) else "N/A"
        median_val = f"{result_stats_data.get('median', 'N/A'):.2f}" if isinstance(result_stats_data.get('median'), (int, float)) else "N/A"
        max_val = f"{result_stats_data.get('max', 'N/A'):.2f}" if isinstance(result_stats_data.get('max'), (int, float)) else "N/A"
        min_val = f"{result_stats_data.get('min', 'N/A'):.2f}" if isinstance(result_stats_data.get('min'), (int, float)) else "N/A"
        q1_val = result_stats_data.get('q1')
        q3_val = result_stats_data.get('q3')
        q_range_val = "N/A"
        if isinstance(q1_val, (int, float)) and isinstance(q3_val, (int, float)):
            q_range_val = f"{q1_val:.2f} - {q3_val:.2f}"

        html_output += f"""
            <tr class="{color_class}">
                <td>{result_key_name}</td>
                <td>{result_stats_data.get('count', 0)}명</td>
                <td>{mean_val}</td>
                <td>{std_val}</td>
                <td>{median_val}</td>
                <td>{max_val}</td>
                <td>{min_val}</td>
                <td>{q_range_val}</td>
            </tr>
        """

    html_output += """
        </tbody>
    </table>
    """
    return html_output

# 새로운 함수: 히스토그램 및 추가 시각화 생성 (수정됨)
def create_advanced_visualizations(plot_id, data):
    """전체 데이터 요약에 대한 추가 시각화 생성

    결과별 분포와 대학별 합격률을 전형유형별로 구분하여 표시한다.
    """
    # 파스텔톤 색상 맵
    color_map = {
        "합격": "#A8D8EA",     # 부드러운 하늘색
        "불합격": "#FFAAA7",   # 부드러운 핑크/연한 빨강
        "충원합격": "#A8E6CE"  # 부드러운 민트색
    }

    apptypes = sorted(data['apptype'].dropna().unique())

    donut_groups = []
    univ_rate_groups = []

    for apptype in apptypes:
        df_app = data[data['apptype'] == apptype]

        # 결과별 도넛 차트
        rc = df_app['result'].value_counts().to_dict()
        v = []
        l = []
        c = []
        for result, count in rc.items():
            v.append(count)
            l.append(result)
            c.append(color_map.get(result, "#666666"))
        
        # Ensure there's data for the donut chart
        if v: # Only create trace if there are values
            donut_trace = f"""{{
                values: {json.dumps(v, cls=NumpyEncoder)},
                labels: {json.dumps(l)},
                type: 'pie',
                hole: 0.6,
                marker: {{ colors: {json.dumps(c)} }},
                textinfo: 'label+percent',
                textposition: 'outside',
                hoverinfo: 'label+value+percent',
                insidetextorientation: 'radial'
            }}"""
            donut_groups.append(f"{{apptype: '{apptype}', traces: [ {donut_trace} ]}}")
        else:
            donut_groups.append(f"{{apptype: '{apptype}', traces: []}}")


        # 대학별 지원자수 기준 합격/불합격 현황
        univ_traces_for_apptype = [] # MODIFICATION: Store valid traces here
        if len(df_app) > 0 and 'univ' in df_app.columns:
            stats = {}
            for univ, grp in df_app.groupby('univ'):
                pass_cnt = len(grp[grp['result'].isin(['합격', '충원합격'])])
                fail_cnt = len(grp[grp['result'] == '불합격'])
                total = pass_cnt + fail_cnt
                # Include all universities regardless of pass count
                if total > 0:
                    stats[univ] = {'total': total, 'pass': pass_cnt, 'fail': fail_cnt}
            
            top_univs = sorted(stats.items(), key=lambda x: x[1]['total'], reverse=True)[:10]
            
            if top_univs:
                univs_list = [u for u, _ in top_univs] # Renamed to avoid conflict
                pass_counts = [d['pass'] for _, d in top_univs]
                fail_counts = [d['fail'] for _, d in top_univs]
                
                # Pass trace
                pass_trace_obj_str = f"""{{
                    y: {json.dumps(univs_list)},
                    x: {json.dumps(pass_counts)},
                    name: '합격',
                    type: 'bar',
                    orientation: 'h',
                    marker: {{ color: '{color_map.get("합격", "#A8D8EA")}' }},
                    hovertemplate: '%{{y}}<br>합격: %{{x}}명<extra></extra>'
                }}"""
                univ_traces_for_apptype.append(pass_trace_obj_str)
                
                # Fail trace
                fail_trace_obj_str = f"""{{
                    y: {json.dumps(univs_list)},
                    x: {json.dumps(fail_counts)},
                    name: '불합격',
                    type: 'bar',
                    orientation: 'h',
                    marker: {{ color: '{color_map.get("불합격", "#FFAAA7")}' }},
                    hovertemplate: '%{{y}}<br>불합격: %{{x}}명<extra></extra>'
                }}"""
                univ_traces_for_apptype.append(fail_trace_obj_str)
        
        # MODIFICATION: Append the group with potentially empty traces array, but always valid syntax
        # This ensures traces is '[]' if univ_traces_for_apptype is empty.
        univ_rate_groups.append(f"{{apptype: '{apptype}', traces: [{', '.join(univ_traces_for_apptype)}]}}")

    # 환산등급 히스토그램 데이터
    conv_grade_histograms = []
    pass_data_conv = data[data["result"].isin(["합격", "충원합격"])]["conv_grade"].dropna()
    if not pass_data_conv.empty: # MODIFICATION: Check if data is not empty
        values_json = json.dumps(pass_data_conv.tolist(), cls=NumpyEncoder)
        conv_grade_histograms.append(f"""{{
            x: {values_json},
            type: 'histogram',
            name: '합격(충원포함)',
            opacity: 0.7,
            marker: {{ color: '{color_map.get("합격", "#A8D8EA")}' }},
            xbins: {{ start: 1, end: 9, size: 0.25 }},
            hoverinfo: 'y+x+name',
            hoverlabel: {{ bgcolor: '{color_map.get("합격", "#A8D8EA")}' }}
        }}""")

    fail_data_conv = data[data["result"] == "불합격"]["conv_grade"].dropna()
    if not fail_data_conv.empty: # MODIFICATION: Check if data is not empty
        values_json = json.dumps(fail_data_conv.tolist(), cls=NumpyEncoder)
        conv_grade_histograms.append(f"""{{
            x: {values_json},
            type: 'histogram',
            name: '불합격',
            opacity: 0.7,
            marker: {{ color: '{color_map.get("불합격", "#FFAAA7")}' }},
            xbins: {{ start: 1, end: 9, size: 0.25 }},
            hoverinfo: 'y+x+name',
            hoverlabel: {{ bgcolor: '{color_map.get("불합격", "#FFAAA7")}' }}
        }}""")

    # 전교과등급 히스토그램 데이터
    all_subj_grade_histograms = []
    pass_data_all_subj = data[data["result"].isin(["합격", "충원합격"])]["all_subj_grade"].dropna()
    if not pass_data_all_subj.empty: # MODIFICATION: Check if data is not empty
        values_json = json.dumps(pass_data_all_subj.tolist(), cls=NumpyEncoder)
        all_subj_grade_histograms.append(f"""{{
            x: {values_json},
            type: 'histogram',
            name: '합격(충원포함)',
            opacity: 0.7,
            marker: {{ color: '{color_map.get("합격", "#A8D8EA")}' }},
            xbins: {{ start: 1, end: 9, size: 0.25 }},
            hoverinfo: 'y+x+name',
            hoverlabel: {{ bgcolor: '{color_map.get("합격", "#A8D8EA")}' }}
        }}""")

    fail_data_all_subj = data[data["result"] == "불합격"]["all_subj_grade"].dropna()
    if not fail_data_all_subj.empty: # MODIFICATION: Check if data is not empty
        values_json = json.dumps(fail_data_all_subj.tolist(), cls=NumpyEncoder)
        all_subj_grade_histograms.append(f"""{{
            x: {values_json},
            type: 'histogram',
            name: '불합격',
            opacity: 0.7,
            marker: {{ color: '{color_map.get("불합격", "#FFAAA7")}' }},
            xbins: {{ start: 1, end: 9, size: 0.25 }},
            hoverinfo: 'y+x+name',
            hoverlabel: {{ bgcolor: '{color_map.get("불합격", "#FFAAA7")}' }}
        }}""")

    donut_groups_js = "[ " + ", ".join(donut_groups) + " ]"
    univ_rate_groups_js = "[ " + ", ".join(univ_rate_groups) + " ]"

    # MODIFICATION: Ensure histogram arrays are correctly formatted as empty '[]' if no traces.
    # The .join() method on an empty list results in an empty string "".
    # So, [ "" ] becomes an empty JS array [].
    conv_hist_js = ", ".join(conv_grade_histograms)
    all_subj_hist_js = ", ".join(all_subj_grade_histograms)

    script = f"""
    <script>
    if (!window.advancedVisualizationData) window.advancedVisualizationData = {{}};
    window.advancedVisualizationData["{plot_id}"] = {{
        donutGroups: {donut_groups_js},
        convGradeHistograms: [ {conv_hist_js} ],
        allSubjGradeHistograms: [ {all_subj_hist_js} ],
        univRateGroups: {univ_rate_groups_js}
    }};
    </script>
    """

    # HTML 컨테이너 생성 (original structure maintained)
    visualizations_html = f"<div class=\"advanced-visualizations-container\">"
    # ... (rest of the HTML generation for containers) ...
    # This part seems okay, assuming the IDs match up with the JS.
    # The key is that the data fed into the JS is now more robust.

    # Example of how HTML containers are generated (shortened)
    for idx, ap in enumerate(apptypes):
        visualizations_html += f"""
        <div class="visualization-row">
            <div class="half-width-visualization">
                <div class="visualization-title">결과별 분포 - {ap}</div>
                <div class="plot-container" id="donut-chart-{plot_id}-{idx}" style="height: 400px;"></div>
            </div>
            <div class="half-width-visualization">
                <div class="visualization-title">대학별 합격률 ({ap})</div>
                <div class="plot-container" id="univ-pass-rates-{plot_id}-{idx}" style="height: 400px;"></div>
            </div>
        </div>"""
    
    # Add histogram containers if they are expected to be there
    # The original code adds these containers unconditionally.
    # It's better if these are also conditional or handled gracefully in JS if data is missing.
    # For now, keeping original structure for HTML containers:
    visualizations_html += f"""
        <div class="visualization-row">
            <div class="full-width-visualization">
                <div class="visualization-title">환산등급 분포 (전체 필터 적용)</div>
                <div class="plot-container" id="conv-grade-histogram-{plot_id}" style="height: 350px;"></div>
            </div>
        </div>
        <div class="visualization-row">
            <div class="full-width-visualization">
                <div class="visualization-title">전교과등급 분포 (전체 필터 적용)</div>
                <div class="plot-container" id="all-subj-grade-histogram-{plot_id}" style="height: 350px;"></div>
            </div>
        </div>
    </div>"""


    # JavaScript 초기화 코드 (original structure maintained)
    # The JS try-catch blocks and g.traces.length checks should now work correctly
    # because the data passed to them will be well-formed.
    init_script = f"""
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        initAdvancedVisualizations("{plot_id}");
    }});

    function initAdvancedVisualizations(plotId) {{
        if (!window.Plotly || !window.advancedVisualizationData || !window.advancedVisualizationData[plotId]) {{
            console.warn('Plotly or advancedVisualizationData not ready for plotId:', plotId);
            return;
        }}

        var data = window.advancedVisualizationData[plotId];

        // 결과별 도넛 차트 (전형유형별)
        if (data.donutGroups) {{
            data.donutGroups.forEach(function(g, idx) {{
                var el = document.getElementById('donut-chart-' + plotId + '-' + idx);
                if (el && g.traces && g.traces.length > 0) {{ // Added g.traces check
                    try {{
                        Plotly.newPlot(el, g.traces, {{
                            title: '',
                            legend: {{ orientation: 'h', y: -0.1, x: 0.5, xanchor: 'center' }},
                            margin: {{ t: 30, b: 50, l: 50, r: 50 }},
                            autosize: true,
                            height: 350,
                            plot_bgcolor: '#FAFAFA',
                            paper_bgcolor: '#FAFAFA'
                        }}, {{ displayModeBar: false, responsive: true }});
                    }} catch (e) {{ console.error('도넛 차트 생성 오류 for ' + g.apptype + ':', e, g.traces); }}
                }} else if (el) {{
                    // console.log('No donut traces for apptype:', g.apptype);
                    // el.innerHTML = '<p style="text-align:center;color:#999;">데이터 없음</p>';
                }}
            }});
        }}

        // 대학별 지원 현황 (전형유형별)
        if (data.univRateGroups) {{
            data.univRateGroups.forEach(function(g, idx) {{
                var el = document.getElementById('univ-pass-rates-' + plotId + '-' + idx);
                // The crucial g.traces.length > 0 check:
                if (el && g.traces && g.traces.length > 0) {{ // Added g.traces check
                    try {{ // This is the try block from user's line 434 context
                        Plotly.newPlot(el, g.traces, {{
                            title: '',
                            showlegend: true,
                            barmode: 'stack',
                            margin: {{ t: 30, b: 50, l: 150, r: 50 }}, // Increased left margin for y-axis labels if needed
                            xaxis: {{ title: '지원자 수 (명)' }},
                            yaxis: {{ automargin: true }}, // automargin can help with long labels
                            autosize: true,
                            height: 350, // Adjust height as needed, especially if many universities
                            plot_bgcolor: '#FAFAFA',
                            paper_bgcolor: '#FAFAFA'
                        }}, {{ displayModeBar: false, responsive: true }});
                    }} catch (e) {{ console.error('대학별 합격률 차트 생성 오류 for ' + g.apptype + ':', e, g.traces); }}
                }} else if (el) {{
                    // console.log('No univ rate traces for apptype:', g.apptype);
                    // el.innerHTML = '<p style="text-align:center;color:#999;">데이터 없음</p>';
                }}
            }});
        }}

        // 환산등급 히스토그램
        var convHistEl = document.getElementById('conv-grade-histogram-' + plotId);
        if (convHistEl && data.convGradeHistograms && data.convGradeHistograms.length > 0) {{
            try {{
                Plotly.newPlot(convHistEl, data.convGradeHistograms, {{
                    title: '',
                    barmode: 'overlay',
                    bargap: 0.1,
                    xaxis: {{ title: '환산등급', range: [1, 9], dtick: 1 }},
                    yaxis: {{ title: '인원 (명)' }},
                    legend: {{ orientation: 'h', y: 1.1, x: 0.5, xanchor: 'center' }},
                    margin: {{ t: 30, b: 60, l: 60, r: 50 }},
                    autosize: true,
                    height: 350,
                    plot_bgcolor: '#FAFAFA',
                    paper_bgcolor: '#FAFAFA'
                }}, {{ displayModeBar: false, responsive: true }});
            }} catch (e) {{ console.error("환산등급 히스토그램 생성 오류:", e, data.convGradeHistograms); }}
        }} else if (convHistEl) {{
            // console.log('No conv grade histogram data.');
            // convHistEl.innerHTML = '<p style="text-align:center;color:#999;">데이터 없음</p>';
        }}


        // 전교과등급 히스토그램
        var allSubjHistEl = document.getElementById('all-subj-grade-histogram-' + plotId);
        if (allSubjHistEl && data.allSubjGradeHistograms && data.allSubjGradeHistograms.length > 0) {{
            try {{
                Plotly.newPlot(allSubjHistEl, data.allSubjGradeHistograms, {{
                    title: '',
                    barmode: 'overlay',
                    bargap: 0.1,
                    xaxis: {{ title: '전교과등급', range: [1, 9], dtick: 1 }},
                    yaxis: {{ title: '인원 (명)' }},
                    legend: {{ orientation: 'h', y: 1.1, x: 0.5, xanchor: 'center' }},
                    margin: {{ t: 30, b: 60, l: 60, r: 50 }},
                    autosize: true,
                    height: 350,
                    plot_bgcolor: '#FAFAFA',
                    paper_bgcolor: '#FAFAFA'
                }}, {{ displayModeBar: false, responsive: true }});
            }} catch (e) {{ console.error("전교과등급 히스토그램 생성 오류:", e, data.allSubjGradeHistograms); }}
        }} else if (allSubjHistEl) {{
            // console.log('No all subj grade histogram data.');
            // allSubjHistEl.innerHTML = '<p style="text-align:center;color:#999;">데이터 없음</p>';
        }}
    }}
    </script>
    """

    return script + visualizations_html + init_script

# The rest of your script (create_stats_html, create_plot_data_script, plot_selected_depts)
# would remain largely the same, as the primary issue seems to be in the data
# preparation within create_advanced_visualizations.
# Make sure that plot_selected_depts calls the corrected create_advanced_visualizations.


# HTML 통계 정보 생성 함수 (기존 코드 유지)
def create_stats_html(stats: dict) -> str:
    """통계 정보를 HTML 형식으로 변환"""
    sc = ''
    sc += f'<div class="stats-item stats-total">총 {stats.get("total_count",0)}명</div>'
    if 'all_pass_count' in stats:
        pr = stats['all_pass_rate'].rstrip('%')
        sc += f'<div class="stats-item stats-pass">합격(전체): {stats["all_pass_count"]}명 <span class="highlight-rate">({pr}%)</span> '
        if all(k in stats for k in ['all_pass_min','all_pass_max','all_pass_mean']):
            sc += f'<span class="highlight-range">등급 {stats["all_pass_min"]:.1f}~{stats["all_pass_max"]:.1f}</span>, <span class="highlight-mean">평균 {stats["all_pass_mean"]:.2f}</span>'
        sc += '</div>'
    if 'pass_count' in stats:
        pr = stats.get('pass_rate', '0.0%').rstrip('%')
        sc += f'<div class="stats-item stats-pass">합격(일반): {stats["pass_count"]}명 <span class="highlight-rate">({pr}%)</span></div>'
    if 'waitlist_count' in stats:
        wr = stats.get('waitlist_rate', '0.0%').rstrip('%')
        sc += f'<div class="stats-item stats-wait">합격(충원): {stats["waitlist_count"]}명 <span class="highlight-rate">({wr}%)</span></div>'
    if 'fail_count' in stats:
        fc = stats['fail_count']
        tc = stats.get('total_count', 1)
        tc = 1 if tc == 0 else tc
        sc += f'<div class="stats-item stats-fail">불합격: {fc}명 <span class="highlight-fail-rate">({fc/tc*100:.1f}%)</span></div>'
    return sc

    # 플롯 데이터 스크립트 생성 함수 (수정됨: 평균 숫자 표시 제거)
def create_plot_data_script(plot_id, data, y_positions, marker_styles, symbol_map=None):
    """
    환산등급과 전교과 등급에 대한 산점도 데이터를 생성하는 JavaScript 코드 반환
    추가 통계 정보를 함께 표시, 결과 순서 변경
    모든 결과 카테고리(합격, 충원합격, 불합격)에 대해 항상 trace 생성
    """
    color_map = {
        "합격": {"border": "#3366CC", "fill": "rgba(51, 102, 204, 0.3)"},
        "불합격": {"border": "#DC3912", "fill": "rgba(220, 57, 18, 0.3)"},
        "충원합격": {"border": "#109618", "fill": "rgba(16, 150, 24, 0.3)"}
    }

    if symbol_map is None:
        symbol_map = {
            "합격": "circle",
            "충원합격": "triangle-up",
            "불합격": "x",
        }
    conv_add_stats = compute_additional_stats(data, "conv_grade")
    all_subj_add_stats = compute_additional_stats(data, "all_subj_grade")
    conv_traces = []
    # conv_means_traces = [] # 평균 숫자 표시 제거

    for result in ["합격", "충원합격", "불합격"]:
        result_data = data[data["result"] == result]
        x_values_conv = result_data["conv_grade"].dropna().tolist()

        if len(x_values_conv) == 0:
            conv_traces.append(f"""{{
                x: [], y: [], type: 'scatter', mode: 'markers', name: '{result}',
                marker: {{ color: '{color_map[result]["fill"]}', line: {{color: '{color_map[result]["border"]}', width: 1.5}}, symbol: '{symbol_map.get(result, "circle")}', size: 12 }},
                showlegend: false, hoverinfo: 'skip'
            }}""")
        else:
            x_values_json = json.dumps(x_values_conv, cls=NumpyEncoder)
            y_values_json = json.dumps([y_positions.get(result, 0)] * len(x_values_conv))
            conv_traces.append(f"""{{
                x: {x_values_json}, y: {y_values_json}, type: 'scatter', mode: 'markers', name: '{result}',
                marker: {{ color: '{color_map[result]["fill"]}', line: {{color: '{color_map[result]["border"]}', width: 1.5}}, symbol: '{symbol_map.get(result, "circle")}', size: 12 }},
                hovertemplate: '환산등급: %{{x}}<br>{result}<extra></extra>'
            }}""")
# 평균값을 표시하는 텍스트 트레이스 추가 (제거됨)
            # conv_means_traces.append(f"""{{
            #     type: 'scatter',
            #     x: ['{result}'],
            #     y: [{mean_value}],
            #     mode: 'text',
            #     text: ['평균: {mean_value:.2f}'],
            #     textposition: 'top center',
            #     textfont: {{ size: 11, color: '{color_map[result]["border"]}', weight: 'bold' }},
            #     showlegend: false,
            #     hoverinfo: 'none'
            # }}""")

    all_subj_traces = []
    # all_subj_means_traces = [] # 평균 숫자 표시 제거

    for result in ["합격", "충원합격", "불합격"]:
        result_data = data[data["result"] == result]
        x_values_all_subj = result_data["all_subj_grade"].dropna().tolist()
        if len(x_values_all_subj) == 0:
            all_subj_traces.append(f"""{{
                x: [], y: [], type: 'scatter', mode: 'markers', name: '{result}',
                marker: {{ color: '{color_map[result]["fill"]}', line: {{color: '{color_map[result]["border"]}', width: 1.5}}, symbol: '{symbol_map.get(result, "circle")}', size: 12 }},
                showlegend: false, hoverinfo: 'skip'
            }}""")
        else:
            x_values_json = json.dumps(x_values_all_subj, cls=NumpyEncoder)
            y_values_json = json.dumps([y_positions.get(result, 0)] * len(x_values_all_subj))
            all_subj_traces.append(f"""{{
                x: {x_values_json}, y: {y_values_json}, type: 'scatter', mode: 'markers', name: '{result}',
                marker: {{ color: '{color_map[result]["fill"]}', line: {{color: '{color_map[result]["border"]}', width: 1.5}}, symbol: '{symbol_map.get(result, "circle")}', size: 12 }},
                hovertemplate: '전교과등급: %{{x}}<br>{result}<extra></extra>'
            }}""")
# 평균값을 표시하는 텍스트 트레이스 추가 (제거됨)
            # all_subj_means_traces.append(f"""{{
            #     type: 'scatter',
            #     x: ['{result}'],
            #     y: [{mean_value}],
            #     mode: 'text',
            #     text: ['평균: {mean_value:.2f}'],
            #     textposition: 'top center',
            #     textfont: {{ size: 11, color: '{color_map[result]["border"]}', weight: 'bold' }},
            #     showlegend: false,
            #     hoverinfo: 'none'
            # }}""")

    conv_stats_html_table = create_additional_stats_html(conv_add_stats, "환산등급", ["합격", "충원합격", "불합격"])
    all_subj_stats_html_table = create_additional_stats_html(all_subj_add_stats, "전교과등급", ["합격", "충원합격", "불합격"])
    script = f"""
    <script>
    if (!window.plotsData) window.plotsData = {{}};
    window.plotsData["{plot_id}"] = {{
        convTraces: [ {", ".join(conv_traces)} ],
        allSubjTraces: [ {", ".join(all_subj_traces)} ]
    }};
    </script>
    """
    # 위 script 문자열에서 conv_means_traces와 all_subj_means_traces 부분을 제거했습니다.
    # 원래 코드: convTraces: [ {", ".join(conv_traces)}, {", ".join(conv_means_traces)} ],
    # 원래 코드: allSubjTraces: [ {", ".join(all_subj_traces)}, {", ".join(all_subj_means_traces)} ]

    return script, conv_stats_html_table, all_subj_stats_html_table

# 새로운 함수: 히스토그램 및 추가 시각화 생성
# 선택된 모집단위에 대한 대학별 시각화 함수 (전형 필터 추가)
def plot_selected_depts(
    df: pd.DataFrame,
    out_dir: Path,
    selected_depts: list = None,
    selected_univs: list = None,
    selected_subtypes: list = None,
    selected_apptypes: list = None,
    output_file: str = "선택된_모집단위들.html",
) -> str:
    """선택된 모집단위에 대한 입시 결과를 대학별로 시각화"""
    # 선택된 모집단위와 대학에 해당하는 데이터만 필터링
    df_filtered = df.copy()

    # 선택된 모집단위 필터링
    if selected_depts:
        df_filtered = df_filtered[df_filtered['dept'].isin(selected_depts)]

    # 선택된 대학 필터링
    if selected_univs:
        df_filtered = df_filtered[df_filtered['univ'].isin(selected_univs)]

    # 선택된 전형 필터링
    if selected_subtypes:
        df_filtered = df_filtered[df_filtered['subtype'].isin(selected_subtypes)]

    # 선택된 전형유형 필터링
    if selected_apptypes:
        df_filtered = df_filtered[df_filtered['apptype'].isin(selected_apptypes)]

    if df_filtered.empty:
        return "선택된 조건에 맞는 데이터가 없습니다."

    # 필터링된 데이터에서 대학 목록 추출 (순서 보존을 위해 사용)
    universities = sorted(df_filtered['univ'].unique())

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>선택된 모집단위 입시 결과</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body, html {{ margin:0; padding:0; font-family:'Malgun Gothic', '맑은 고딕', sans-serif; background-color: #f4f7f6; }}
            .fixed-header {{ position: sticky; top: 0; background-color: white; padding: 10px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); z-index: 1000; width: 100%; border-bottom: 1px solid #ddd; }}
            .header-content {{ max-width: 1200px; margin: 0 auto; padding: 0 20px; display: flex; flex-direction: column; align-items: center; }}
            .university-title {{ text-align: center; font-size: 24px; margin: 10px 0 15px; font-weight: bold; color: #333; }}
            .controls-legend-wrapper {{ display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 10px; flex-wrap: wrap; }}
            .grade-toggle-container {{ padding: 10px; background-color: #f8f8f8; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); flex: 1; min-width: 280px; margin-right: 10px; text-align: center; }}
            .grade-toggle-btn {{ padding: 10px 18px; margin: 0 5px; font-size: 14px; cursor: pointer; border: 1px solid #ccc; border-radius: 6px; background-color: white; transition: all 0.2s ease-in-out; font-weight: 500; }}
            .grade-toggle-btn:hover {{ background-color: #e9e9e9; border-color: #bbb; }}
            .grade-toggle-btn.active {{ background-color: #007bff; color: white; border-color: #0056b3; box-shadow: 0 0 5px rgba(0,123,255,0.5); }}
            .legend-container {{ display: flex; flex-direction: column; align-items: flex-start; flex: 1; min-width: 300px; background-color: #f8f8f8; padding: 10px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
            .legend-items-wrapper {{ display: flex; justify-content: flex-start; margin-bottom: 8px; flex-wrap: wrap; }}
            .legend-item {{ display: inline-flex; align-items: center; margin: 5px 10px 5px 0; }}
            .legend-marker {{ font-size: 18px; margin-right: 6px; display: inline-flex; align-items: center; justify-content: center; }}
            .legend-pass {{ color: #3366CC; }}
            .legend-wait {{ color: #109618; }}
            .legend-fail {{ color: #DC3912; }}
            .legend-text {{ font-size: 14px; color: #333; }}
            .axis-label {{ font-size: 13px; color: #505050; font-weight: bold; margin-top: 5px; }}
            .axis-icon {{ font-size: 16px; margin-right: 5px; }}
            .layout {{ display: flex; justify-content: center; align-items: flex-start; max-width: 1200px; margin: 20px auto; padding: 0 20px; }}
            .toc-container {{ flex: 0 0 220px; position: sticky; top: 160px; margin-right: 25px; background-color: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; max-height: calc(100vh - 200px); overflow-y: auto; box-shadow: 0 4px 12px rgba(0,0,0,0.08); z-index: 900; }}
            .toc-header {{ font-weight: bold; font-size: 18px; margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px; color: #333; }}
            .toc-university {{ font-weight: bold; margin-top: 10px; cursor: pointer; padding: 6px 8px; border-radius: 4px; transition: background-color 0.2s; color: #0056b3; display:flex; align-items:center; }}
            .toc-university:hover {{ background-color: #e9ecef; }}
            .toc-arrow {{ margin-right: 6px; }}
            .toc-subitems {{ margin-left: 18px; display:none; }}
            .toc-subtype-item {{ font-size: 0.9em; cursor: pointer; padding: 5px 8px; border-radius: 4px; transition: background-color 0.2s; color: #333; }}
            .toc-subtype-item:hover {{ background-color: #f1f3f5; }}
            .main-content {{ flex: 1 1 auto; max-width: calc(100% - 245px); padding-top: 20px; }}
            .dept-container {{ margin-bottom: 50px; border: 1px solid #d1d9e6; border-radius: 12px; padding: 25px; background-color: #ffffff; box-shadow: 0 6px 18px rgba(0,0,0,0.07); }}
            .dept-header {{ margin-bottom: 20px; font-weight: bold; font-size: 22px; color: #2c3e50; border-bottom: 2px solid #007bff; padding-bottom: 12px; }}
            .subtype-container {{ margin-bottom: 30px; border: 1px solid #e7eaf0; border-radius: 8px; padding: 20px; background-color: #fdfdfd; }}
            .subtype-header {{ margin-bottom: 15px; font-weight: bold; font-size: 18px; color: #34495e; }}
            .visualization-container {{ display: flex; flex-direction: column; width: 100%; margin-bottom: 20px; }}
            .plot-stats-wrapper {{ width: 100%; margin-bottom: 10px; }}
            .stats-container {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }}
            .stats-item {{ padding: 6px 12px; border-radius: 6px; background-color: #f0f4f7; white-space: nowrap; font-size: 14px; color: #333; border: 1px solid #d6dde3; }}
            .stats-total {{ font-weight: bold; background-color: #e2e8ef; border-color: #c8d0d8; }}
            .stats-pass {{ border-left: 4px solid #007bff; }}
            .stats-wait {{ border-left: 4px solid #28a745; }}
            .stats-fail {{ border-left: 4px solid #dc3545; }}
            .highlight-rate, .highlight-fail-rate {{ font-weight: bold; }}
            .highlight-rate {{ color: #0056b3; }}
            .highlight-fail-rate {{ color: #c82333; }}
            .highlight-mean {{ font-weight: bold; color: #1e7e34; }}
            .highlight-range {{ color: #5a6268; font-size: 13px; }}
            .plot-container {{ height: 200px; width: 100%; margin: 0 auto; }}
            .stats-tables-wrapper {{ width: 100%; margin-bottom: 30px; }}
            .additional-stats-container {{ width: 100%; padding: 10px 0; background-color: transparent; border-radius: 0; font-size: 13px; }}
            .stats-detail-title {{ font-weight: bold; margin-bottom: 8px; color: #333; font-size: 15px; }}
            .stats-table {{ width: 100%; border-collapse: collapse; margin-top: 8px; table-layout: fixed; }}
            .stats-table th, .stats-table td {{ padding: 8px; text-align: center; border: 1px solid #dee2e6; }}
            .stats-table th {{ background-color: #e9ecef; font-weight: bold; color: #495057; }}
            .stats-table .pass-row td {{ background-color: rgba(0, 123, 255, 0.05); }}
            .stats-table .fail-row td {{ background-color: rgba(220, 53, 69, 0.05); }}
            .stats-table .waitlist-row td {{ background-color: rgba(40, 167, 69, 0.05); }}
            .no-stats {{ font-style: italic; color: #6c757d; text-align: center; padding: 15px; }}
            /* 추가 시각화를 위한 스타일 */
            .advanced-visualizations-container {{ width: 100%; margin-top: 20px; }}
            .visualization-row {{ display: flex; margin-bottom: 30px; gap: 20px; flex-wrap: wrap; }}
            .half-width-visualization {{ flex: 1 1 calc(50% - 10px); min-width: 400px; background-color: #FFFFFF; border-radius: 12px; padding: 20px; box-shadow: 0 3px 10px rgba(0,0,0,0.05); }}
            .full-width-visualization {{ flex: 1 1 100%; background-color: #FFFFFF; border-radius: 12px; padding: 20px; box-shadow: 0 3px 10px rgba(0,0,0,0.05); }}
            .visualization-title {{ font-weight: bold; font-size: 16px; margin-bottom: 15px; color: #506380; text-align: center; }}
            @media (max-width: 992px) {{
                .layout {{ flex-direction: column; align-items: center; }}
                .toc-container {{ position: static; width: 100%; max-width: 600px; margin-right: 0; margin-bottom: 20px; max-height: 300px; }}
                .main-content {{ max-width: 100%; width: 100%; }}
                .controls-legend-wrapper {{ flex-direction: column; align-items: stretch; }}
                .grade-toggle-container, .legend-container {{ width: auto; margin-right: 0; margin-bottom: 10px; }}
                .visualization-row {{ flex-direction: column; }}
                .half-width-visualization {{ min-width: 100%; margin-bottom: 15px; }}
            }}
            @media (max-width: 768px) {{
                .fixed-header {{ padding: 5px 0; }}
                .header-content {{ padding: 0 10px; }}
                .university-title {{ font-size: 20px; margin-bottom: 10px; }}
                .grade-toggle-btn {{ padding: 8px 12px; font-size: 13px; }}
                .legend-item {{ margin: 3px 8px 3px 0; }}
                .legend-text, .axis-label {{ font-size: 12px; }}
                .dept-header {{ font-size: 20px; }}
                .subtype-header {{ font-size: 17px; }}
                .stats-item {{ font-size: 13px; padding: 5px 10px; }}
                .plot-container {{ height: 200px; }}
                .additional-stats-container {{ padding: 10px 0; }}
                .stats-detail-title {{ font-size: 14px; }}
                .stats-table th, .stats-table td {{ padding: 6px; }}
            }}
            .filter-info-container {{
                margin: 15px 0;
                background-color: #e9f7fe;
                border: 1px solid #b8e3ff;
                padding: 15px;
                border-radius: 8px;
            }}
            .filter-info-container h3 {{
                margin-top: 0;
                color: #0275d8;
                font-size: 16px;
                margin-bottom: 10px;
            }}
            .filter-info-container ul {{
                margin: 0;
                padding-left: 20px;
            }}
            .filter-info-container li {{
                margin-bottom: 5px;
                font-size: 14px;
            }}
        </style>

    </head>
    <body>
        <div class="fixed-header">
            <div class="header-content">
                <div class="university-title">선택된 모집단위 입시 결과</div>
                <div class="controls-legend-wrapper">
                    <div class="grade-toggle-container">
                        <button id="btn-conv-grade" class="grade-toggle-btn" onclick="switchGradeType('conv')">환산등급</button>
                        <button id="btn-all-subj-grade" class="grade-toggle-btn active" onclick="switchGradeType('all_subj')">전교과100 등급</button>
                    </div>
                    <div class="legend-container">
                        <div class="legend-items-wrapper">
                            <div class="legend-item"><span class="legend-marker legend-pass">&#9679;</span><span class="legend-text">합격 (Y축 상단)</span></div>
                            <div class="legend-item"><span class="legend-marker legend-wait">&#9650;</span><span class="legend-text">충원합격 (Y축 중앙)</span></div>
                            <div class="legend-item"><span class="legend-marker legend-fail">&#10006;</span><span class="legend-text">불합격 (Y축 하단)</span></div>
                        </div>
                        <div class="axis-label"><span class="axis-icon">↔</span> X축: <span id="grade-type-label">전교과100 등급</span> (1등급 ~ 9등급)</div>
                    </div>
                </div>
            </div>
        </div>
        <div class="layout">
            <aside class="toc-container">
                <div class="toc-header">목차</div>
                <div id="toc-content"></div>
            </aside>
            <main class="main-content">\n"""

    y_positions = {"합격":0.01, "충원합격":0.0, "불합격":-0.03}
    marker_styles = {
        "합격": {"opacity":0.7, "line":dict(width=1.5, color="blue"), "color":"rgba(0,0,255,0.3)"},
        "불합격": {"opacity":0.6, "line":dict(width=0.7, color="red"), "color":"rgba(255,0,0,0.2)"},
        "충원합격": {"opacity":0.7, "line":dict(width=1.2, color="steelblue"), "color":"rgba(70,130,180,0.3)"}
    }
    plot_counter = 1

    for univ_idx, univ in enumerate(universities, 1):
        # 현재 대학 + 선택된 모집단위에 해당하는 데이터 필터링
        df_univ = df_filtered[df_filtered['univ'] == univ]
        html_content += f"""
        <div class="dept-container" id="univ-{univ_idx}">
            <div class="dept-header">{univ}</div>
        """

        # 전형유형별 요약 먼저 추가
        ap_summary_container_id = f"apptype-summary-{univ_idx}"
        html_content += f"""
        <div class="subtype-container" id="{ap_summary_container_id}" style="background-color: #eef2f7;">
            <div class="subtype-header" style="color: #1a202c;">전형유형별 요약</div>
        """

        if selected_apptypes:
            apptypes_all = sorted(set(df_univ['apptype']) & set(selected_apptypes))
        else:
            apptypes_all = sorted(df_univ['apptype'].unique())

        for a_idx, apptype in enumerate(apptypes_all, 1):
            ss = df_univ[df_univ['apptype'] == apptype]

            if selected_depts:
                ss = ss[ss['dept'].isin(selected_depts)]
                if ss.empty:
                    continue
            if selected_subtypes:
                ss = ss[ss['subtype'].isin(selected_subtypes)]
                if ss.empty:
                    continue

            conv_stats = compute_stats(ss, "conv_grade")
            all_subj_stats = compute_stats(ss, "all_subj_grade")
            conv_stats_html = create_stats_html(conv_stats)
            all_subj_stats_html = create_stats_html(all_subj_stats)

            plot_script, conv_detail_stats, all_subj_detail_stats = create_plot_data_script(
                plot_counter, ss, y_positions, marker_styles
            )

            html_content += f"""
                <div class="subtype-container" id="apptype-{univ_idx}-{a_idx}" style="margin-left: 20px; background-color: #fbfcfe;">
                    <div class="subtype-header" style="font-size: 16px; color: #4a5568;">{apptype}</div>
                    <div class="visualization-container">
                        <div class="plot-stats-wrapper">
                            <div id="conv-stats-{plot_counter}" class="stats-container" style="display:none;">{conv_stats_html}</div>
                            <div id="all-subj-stats-{plot_counter}" class="stats-container">{all_subj_stats_html}</div>
                            <div class="plot-container" id="plot-{plot_counter}"></div>
                        </div>
                        {plot_script}
                    </div>
                </div>
            """
            plot_counter += 1

        html_content += """
        </div>
        """

        # 각 대학에서 모집단위 목록 가져오기
        if selected_depts:
            univ_depts = sorted(set(df_univ['dept']) & set(selected_depts))
        else:
            univ_depts = sorted(df_univ['dept'].unique())

        # 모집단위별 루프
        for d_idx, dept in enumerate(univ_depts, 1):
            dd = df_univ[df_univ['dept'] == dept]

            html_content += f"""
            <div class="subtype-container" id="dept-container-{univ_idx}-{d_idx}">
                <div class="subtype-header" style="color: #34495e;">{d_idx}) {dept}</div>
            """

            # 선택된 전형 목록 가져오기
            if selected_subtypes:
                dept_subtypes = sorted(set(dd['subtype']) & set(selected_subtypes))
            else:
                dept_subtypes = sorted(dd['subtype'].unique())

            # 전형별 루프
            for st_idx, subtype_val in enumerate(dept_subtypes, 1):
                st_data = dd[dd['subtype'] == subtype_val]
                if st_data.empty:
                    continue

                conv_stats = compute_stats(st_data, "conv_grade")
                all_subj_stats = compute_stats(st_data, "all_subj_grade")
                conv_stats_html = create_stats_html(conv_stats)
                all_subj_stats_html = create_stats_html(all_subj_stats)

                plot_script, conv_detail_stats, all_subj_detail_stats = create_plot_data_script(
                    plot_counter, st_data, y_positions, marker_styles
                )

                html_content += f"""
                <div class="subtype-container" id="subtype-{univ_idx}-{d_idx}-{st_idx}" style="margin-left: 20px; background-color: #fbfcfe;">
                    <div class="subtype-header" style="font-size: 16px; color: #4a5568;">{st_idx}) {subtype_val}</div>
                    <div class="visualization-container">
                        <div class="plot-stats-wrapper">
                            <div id="conv-stats-{plot_counter}" class="stats-container" style="display:none;">{conv_stats_html}</div>
                            <div id="all-subj-stats-{plot_counter}" class="stats-container">{all_subj_stats_html}</div>
                            <div class="plot-container" id="plot-{plot_counter}"></div>
                        </div>
                        {plot_script}
                    </div>
                </div>
                """
                plot_counter += 1

            html_content += """
            </div>
            """

        # 대학별 전형 요약 섹션 (이전 코드와 유사)
        summary_container_id = f"summary-container-{univ_idx}"
        html_content += f"""
        <div class="subtype-container" id="{summary_container_id}" style="background-color: #eef2f7;">
            <div class="subtype-header" style="color: #1a202c;">전형별 요약</div>
        """

        # 전형 목록 가져오기
        if selected_subtypes:
            subtypes_all = sorted(set(df_univ['subtype']) & set(selected_subtypes))
        else:
            subtypes_all = sorted(df_univ['subtype'].unique())

        for s_idx, subtype in enumerate(subtypes_all, 1):
            # 해당 전형의 모든 데이터 추출
            ss = df_univ[df_univ['subtype'] == subtype]

            # 선택된 모집단위 필터링 적용
            if selected_depts:
                ss = ss[ss['dept'].isin(selected_depts)]
                if ss.empty:
                    continue

            # 통계 계산
            conv_stats = compute_stats(ss, "conv_grade")
            all_subj_stats = compute_stats(ss, "all_subj_grade")
            conv_stats_html = create_stats_html(conv_stats)
            all_subj_stats_html = create_stats_html(all_subj_stats)

            # 박스플롯 스크립트 및 통계 테이블 생성
            plot_script, conv_detail_stats, all_subj_detail_stats = create_plot_data_script(
                plot_counter, ss, y_positions, marker_styles
            )

            html_content += f"""
                <div class="subtype-container" id="subtype-summary-{univ_idx}-{s_idx}" style="margin-left: 20px; background-color: #fbfcfe;">
                    <div class="subtype-header" style="font-size: 16px; color: #4a5568;">{subtype}</div>
                    <div class="visualization-container">
                        <div class="plot-stats-wrapper">
                            <div id="conv-stats-{plot_counter}" class="stats-container" style="display:none;">{conv_stats_html}</div>
                            <div id="all-subj-stats-{plot_counter}" class="stats-container">{all_subj_stats_html}</div>
                            <div class="plot-container" id="plot-{plot_counter}"></div>
                        </div>
                        {plot_script}
                    </div>
                </div>
            """
            plot_counter += 1

        html_content += """
        </div>
        </div>
        """

    # 전체 데이터 요약 섹션 추가
    html_content += """
    <div class="dept-container" id="overall-summary">
        <div class="dept-header" style="color: #2c3e50; border-bottom: 2px solid #e74c3c;">전체 데이터 요약</div>
        <div class="subtype-container" style="background-color: #f8f9fa;">
            <div class="subtype-header" style="color: #1a202c;">선택된 모든 필터에 대한 종합 분석</div>
    """

    # 전체 필터링된 데이터에 대한 통계 계산
    overall_conv_stats = compute_stats(df_filtered, "conv_grade")
    overall_all_subj_stats = compute_stats(df_filtered, "all_subj_grade")
    overall_conv_stats_html = create_stats_html(overall_conv_stats)
    overall_all_subj_stats_html = create_stats_html(overall_all_subj_stats)

    # 박스플롯 스크립트 및 통계 테이블 생성
    overall_plot_script, overall_conv_detail_stats, overall_all_subj_detail_stats = create_plot_data_script(
        plot_counter, df_filtered, y_positions, marker_styles
    )

    html_content += f"""
        <div class="visualization-container">
            <div class="plot-stats-wrapper">
                <div id="conv-stats-{plot_counter}" class="stats-container" style="display:none;">{overall_conv_stats_html}</div>
                <div id="all-subj-stats-{plot_counter}" class="stats-container">{overall_all_subj_stats_html}</div>
                <div class="plot-container" id="plot-{plot_counter}"></div>
            </div>
            {overall_plot_script}
            <div class="stats-tables-wrapper">
                <div id="conv-additional-stats-{plot_counter}" class="additional-stats-container" style="display:none;">
                    {overall_conv_detail_stats}
                </div>
                <div id="all-subj-additional-stats-{plot_counter}" class="additional-stats-container">
                    {overall_all_subj_detail_stats}
                </div>
            </div>
        </div>
    """

    # 추가 시각화 생성 - 전체 데이터 요약에 대한 추가 그래프
    additional_visualizations = create_advanced_visualizations(plot_counter, df_filtered)
    html_content += additional_visualizations

    # 선택된 필터 정보 표시 (옵션)
    filter_info = []
    if selected_univs:
        univ_count = len(selected_univs)
        univ_text = f"{univ_count}개 대학" if univ_count > 3 else ", ".join(selected_univs)
        filter_info.append(f"선택된 대학: {univ_text}")
    if selected_subtypes:
        subtype_count = len(selected_subtypes)
        subtype_text = f"{subtype_count}개 전형" if subtype_count > 3 else ", ".join(selected_subtypes)
        filter_info.append(f"선택된 전형: {subtype_text}")
    if selected_depts:
        dept_count = len(selected_depts)
        dept_text = f"{dept_count}개 모집단위" if dept_count > 3 else ", ".join(selected_depts)
        filter_info.append(f"선택된 모집단위: {dept_text}")

    if filter_info:
        filter_info_html = "<div class='filter-info-container'><h3>적용된 필터</h3><ul>"
        for info in filter_info:
            filter_info_html += f"<li>{info}</li>"
        filter_info_html += "</ul></div>"
        html_content += filter_info_html

    html_content += """
        </div>
    </div>
    """

    plot_counter += 1

    html_content += """
    <script>
    var currentGradeType = 'all_subj';
    var plotsInitialized = false;
    document.addEventListener('DOMContentLoaded', function() {
        console.log('페이지 초기화 시작...');
        var toc = document.getElementById('toc-content');
        var tocHTML = '';

        // 대학별 컨테이너 순회
        document.querySelectorAll('.dept-container').forEach(function(container) {
            var uniId = container.id;
            var uniHeader = container.querySelector('.dept-header');
            if (!uniHeader) return; // dept-header가 없는 경우 건너뛰기 (예: 전체 요약)
            var uniTitle = uniHeader.textContent;

            // '전체 데이터 요약'은 별도로 처리
            if (uniId === 'overall-summary') return;

            var subId = 'toc-' + uniId;
            tocHTML += `<div class="toc-university" onclick="toggleToc('${subId}', this); scrollToElement('${uniId}')"><span class="toc-arrow">▶</span>${uniTitle}</div>`;
            tocHTML += `<div class="toc-subitems" id="${subId}">`;

            var apSummary = container.querySelector('[id^="apptype-summary-"]');
            if (apSummary) {
                tocHTML += `<div class="toc-subtype-item" onclick="scrollToElement('${apSummary.id}')">전형유형별 요약</div>`;
            }

            container.querySelectorAll('[id^="dept-container-"]').forEach(function(deptContainer) {
                var deptHeader = deptContainer.querySelector('.subtype-header');
                if (deptHeader) {
                    var deptId = deptContainer.id;
                    var deptTitle = deptHeader.textContent.replace(/^\\d+\\)\\s*/, '').trim();
                    tocHTML += `<div class="toc-dept-item" style="margin-left: 18px; font-weight: bold; margin-top: 8px; color: #0056b3;" onclick="scrollToElement('${deptId}')">${deptTitle}</div>`;
                }
            });

            tocHTML += `</div>`;
        });

        // 전체 요약 섹션 목차에 추가
        var overallSummaryElem = document.getElementById('overall-summary');
        if (overallSummaryElem) {
            var overallHeader = overallSummaryElem.querySelector('.dept-header');
            if (overallHeader) {
                 tocHTML += `<div class="toc-university" onclick="scrollToElement('overall-summary')" style="margin-top: 20px; color: #e74c3c;">${overallHeader.textContent}</div>`;
            }
        }
        toc.innerHTML = tocHTML;
        initializeAllPlots();

    });

    function initializeAllPlots() {
        if (plotsInitialized || !window.Plotly) return;
        console.log('모든 플롯 초기화 중...');
        var plotContainers = document.querySelectorAll('.plot-container[id^="plot-"]');
        plotContainers.forEach(function(plotDiv) {
            var plotId = plotDiv.id;
            var numericId = plotId.split('-')[1];
            try {
                // 기본 박스플롯 처리
                if(plotId.startsWith('plot-')) {
                    if (!window.plotsData || !window.plotsData[numericId]) {
                        console.error('플롯 데이터를 찾을 수 없음:', numericId);
                        plotDiv.innerHTML = '<p style="text-align:center; color:red;">플롯 데이터 로드 실패</p>';
                        return;
                    }
                    var plotData = window.plotsData[numericId];
                    var traces = JSON.parse(JSON.stringify(
                        currentGradeType === 'conv' ? plotData.convTraces : plotData.allSubjTraces
                    ));
                    var layout = createPlotLayout();
                    Plotly.newPlot(plotDiv, traces, layout, {displayModeBar: false, responsive: true, useResizeHandler: true});
                }
                // 추가 시각화는 별도 함수로 처리됨 (donut-chart, histograms 등)
            } catch (error) {
                console.error(`플롯 ${numericId} 초기화 오류:`, error);
                plotDiv.innerHTML = `<p style="text-align:center; color:red;">플롯 생성 중 오류 발생: ${error.message}</p>`;
            }
        });
        plotsInitialized = true;
        console.log('모든 플롯 초기화 완료');
    }

    function createPlotLayout() {
        return {
            height: 200,
            autosize: true,
            margin: {t: 15, b: 50, l: 60, r: 30},
            bargap: 0.2,
            xaxis: {
                range: [0.5, 9.5],
                showgrid: true,
                gridcolor: [
                    '#e0e0e0', '#b0b0b0', '#e0e0e0', '#b0b0b0', '#e0e0e0',
                    '#b0b0b0', '#e0e0e0', '#b0b0b0', '#e0e0e0'
                ],
                gridwidth: [
                    0.5, 1.0, 0.5, 1.0, 0.5, 1.0, 0.5, 1.0, 0.5
                ],
                griddash: [
                    'dot','solid','dot','solid','dot','solid','dot','solid','dot'
                ],
                title: { text: '등급', font: { size: 13, color: '#333' }},
                autorange: false,
                tickmode: 'array',
                tickvals: [1,2,3,4,5,6,7,8,9],
                ticktext: ['1','2','3','4','5','6','7','8','9'],
                tickfont: {
                    size: 11,
                    color: ['#7f7f7f','#333333','#7f7f7f','#333333','#7f7f7f','#333333','#7f7f7f','#333333','#7f7f7f']
                }
            },
            yaxis: {
                showgrid: false,
                autorange: false,
                range: [-0.05, 0.05],
                zeroline: false,
                showline: false,
                tickmode: 'array',
                tickvals: [0.01, 0.0, -0.03],
                // 여기서 티커 텍스트를 비워둠 - 모든 그래프의 Y축 레이블 제거
                ticktext: ['', '', ''],
                tickfont: { size: 14 }
            },
            plot_bgcolor: "white",
            paper_bgcolor: "white",
            showlegend: false,
        };
    }

    function switchGradeType(gradeType) {
        if (currentGradeType === gradeType || !window.Plotly) return;
        console.log("등급 전환: " + gradeType);
        currentGradeType = gradeType;
        document.getElementById('btn-conv-grade').classList.toggle('active', gradeType === 'conv');
        document.getElementById('btn-all-subj-grade').classList.toggle('active', gradeType === 'all_subj');
        document.getElementById('grade-type-label').textContent = gradeType === 'conv' ? '환산등급' : '전교과100 등급';

        var overallSummaryPlotId = null;
        var overallSummaryContainer = document.getElementById('overall-summary');
        if (overallSummaryContainer) {
            var plotContainer = overallSummaryContainer.querySelector('.plot-container[id^="plot-"]');
            if (plotContainer) {
                overallSummaryPlotId = plotContainer.id.split('-')[1];
            }
        }


        updateAllPlots(gradeType); // 먼저 박스플롯들을 업데이트
        
        // 통계 정보 및 상세 통계 테이블 가시성 업데이트
        document.querySelectorAll('.plot-stats-wrapper').forEach(function(wrapper) {
            var plotId = wrapper.querySelector('.plot-container[id^="plot-"]').id.split('-')[1];
            
            var convStatsElem = document.getElementById('conv-stats-' + plotId);
            var allSubjStatsElem = document.getElementById('all-subj-stats-' + plotId);
            var convAddStatsElem = document.getElementById('conv-additional-stats-' + plotId);
            var allSubjAddStatsElem = document.getElementById('all-subj-additional-stats-' + plotId);

            if (convStatsElem) convStatsElem.style.display = (gradeType === 'conv') ? 'flex' : 'none';
            if (allSubjStatsElem) allSubjStatsElem.style.display = (gradeType === 'all_subj') ? 'flex' : 'none';
            if (convAddStatsElem) convAddStatsElem.style.display = (gradeType === 'conv') ? 'block' : 'none';
            if (allSubjAddStatsElem) allSubjAddStatsElem.style.display = (gradeType === 'all_subj') ? 'block' : 'none';
        });
        
        // 전체 데이터 요약 섹션의 히스토그램 가시성 업데이트
        if (overallSummaryPlotId) {
            var convHistogram = document.getElementById('conv-grade-histogram-' + overallSummaryPlotId);
            var allSubjHistogram = document.getElementById('all-subj-grade-histogram-' + overallSummaryPlotId);
            
            if (convHistogram) convHistogram.style.display = (gradeType === 'conv') ? 'block' : 'none';
            if (allSubjHistogram) allSubjHistogram.style.display = (gradeType === 'all_subj') ? 'block' : 'none';
        }
    }

    function updateAllPlots(gradeType) {
        console.log('모든 플롯 업데이트 중... 타입:', gradeType);
        var plotContainers = document.querySelectorAll('.plot-container[id^="plot-"]');
        plotContainers.forEach(function(plotDiv) {
            var plotId = plotDiv.id;
            var numericId = plotId.split('-')[1]; // plot-container의 ID에서 숫자 부분 추출
            try {
                if (!window.plotsData || !window.plotsData[numericId]) {
                    console.error('플롯 데이터를 찾을 수 없음 (update):', numericId);
                    return;
                }
                var plotData = window.plotsData[numericId];
                var traces;
                if (gradeType === 'conv') {
                    traces = JSON.parse(JSON.stringify(plotData.convTraces));
                } else {
                    traces = JSON.parse(JSON.stringify(plotData.allSubjTraces));
                }
                var layout = createPlotLayout();
                Plotly.react(plotDiv, traces, layout, {displayModeBar: false, responsive: true, useResizeHandler: true});
            } catch (error) {
                console.error(`플롯 ${numericId} 업데이트 오류:`, error);
                // plotDiv.innerHTML = `<p style="text-align:center; color:red;">플롯 업데이트 중 오류 발생: ${error.message}</p>`;
            }
        });
        console.log('모든 플롯 업데이트 완료');
    }

    function toggleToc(id, headerEl) {
        var el = document.getElementById(id);
        if (!el) return;
        var hidden = el.style.display === 'none' || el.style.display === '';
        el.style.display = hidden ? 'block' : 'none';
        if (headerEl) {
            var arrow = headerEl.querySelector('.toc-arrow');
            if (arrow) arrow.textContent = hidden ? '▼' : '▶';
        }
    }

    function scrollToElement(id) {
        var el = document.getElementById(id);
        if (el) {
            var headerHeight = document.querySelector('.fixed-header').offsetHeight;
            var elementPosition = el.getBoundingClientRect().top + window.pageYOffset;
            var offsetPosition = elementPosition - headerHeight - 20; // 20px 추가 여백
            window.scrollTo({ top: offsetPosition, behavior: 'smooth' });
            // 하이라이트 효과 (선택 사항)
            el.style.transition = 'background-color 0.5s ease-out';
            el.style.backgroundColor = 'rgba(255, 223, 186, 0.5)'; // 연한 주황색 하이라이트
            setTimeout(function() { el.style.backgroundColor = ''; }, 1500); // 1.5초 후 원래대로
        }
    }
    </script>
    """
    html_content += """
            </main>
        </div>
    </body>
    </html>
    """

    output_path = out_dir / output_file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return f"{output_path.resolve()} 파일이 생성되었습니다."
    except Exception as e:
        return f"파일 저장 중 오류 발생: {e}"