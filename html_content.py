scoreTable_head = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>成績表</title>
        <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #EEEEEE;
        }
        h1{
            text-align: center;
            font-size: 40px;
            color: #222222;
        }
        table {
            border-collapse: separate;
            border-spacing: 0;
            border-radius: 10px;
            width: 100%;
            margin: 30px;
            border: 2px solid #CCCCCC;
        }
        th, td {
            text-align: left;
            padding: 8px;
        }
        tr:nth-child(even) {
            background-color: #CCCCCC;
        }
        th {
            height: 30px;
        }
        #score-table{
            font-family: Arial, sans-serif;
            display: flex;
            margin: 0;
            padding: 0px;
        }
        .info-bar {
            display: flex;
            justify-content: space-around;
            margin: 20px 30px;
            margin-bottom: 0px;
        }
        .info-item {
            font-weight: bolder;
            font-size: 20px;
        }
        </style>
    </head>
    <body>
    """

scoreTable_table = f"""
        <div id="score-table">
        <table>
            <tr>
                <th>課號</th>
                <th>學分</th>
                <th>選別</th>
                <th>課名</th>
                <th>教授</th>
                <th>暫定成績</th>
                <th>最終成績</th>
            </tr>
    """

schedule_head = """
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <title>課程表</title>
<style>
    @font-face {
        font-family: 'GenSenRounded-M';
        src:  url('GenSenRounded-M.ttc') format("truetype"); 
    }
    body {
        font-family: 'GenSenRounded-M',Arial, sans-serif;
        /* font-weight: 600; */
        background-color: #eeeeee;
    }
    table {
        width: 1200px;
        height: 100dvh;
        border-collapse: separate;
        border-spacing: 6px;
        /* 調整間距 */
        
        table-layout: fixed;
        /* 使每列寬度一致 */
    }
    th,td {
        /* height: 105px; */
        padding: 10px;
        text-align:center;
        font-size: 15px;
        /* 統一格子的高度 */
    }
    th {
        font-size: 15px;
        background-color: transparent;
        /* 標題無背景色 */
    }
    .class-cell {
        background-color: rgba(2, 2, 2, 0.74);
        /* 半透明淺黑色背景 */
        border-radius: 30px;
        color: rgba(255, 255, 255, 0.925);
    }
    .no-class {
        background-color: transparent;
        /* 無課程無背景色 */
    }
</style>
</head>
<body>
    <table id="schedule">
    </table>
    <script>
        // 定義課程表數據
        const scheduleData ="""

schedule_tail = """
        // 函數用於動態添加課程表到HTML
       function loadSchedule() {
            const table = document.getElementById('schedule');
            scheduleData.forEach((row, rowIndex) => {
                const tr = document.createElement('tr');
                row.forEach((cell, cellIndex) => {
                    if (rowIndex > 0 && cellIndex > 0 && cell.trim() === scheduleData[rowIndex - 1][cellIndex].trim() && cell.trim() !== '') {
                        // 跳過重複的課程以實現合併效果
                        return;
                    }
                    cell = cell.replace(/\\n\\n\\t$/, '');
                    const td = document.createElement(rowIndex === 0 || cellIndex === 0 ? 'th' : 'td');
                    td.innerHTML = cell.trim() === '' ? '&nbsp;' : cell.replace(/\\n/g, '<br>');
                    if (rowIndex > 0 && cellIndex > 0 && cell.trim() !== '') {
                        td.classList.add('class-cell');
                        let rowspan = 1;
                        for (let i = rowIndex + 1; i < scheduleData.length && scheduleData[i][cellIndex].trim() === cell.trim(); i++) {
                            rowspan++;
                        }
                        if (rowspan > 1) {
                            td.setAttribute('rowspan', rowspan.toString());
                        }
                    }
                    tr.appendChild(td);
                });
                table.appendChild(tr);
            });
        }

        // 當頁面加載完成後，執行loadSchedule函數
        window.onload = loadSchedule;
    </script>

</body>

</html>
"""