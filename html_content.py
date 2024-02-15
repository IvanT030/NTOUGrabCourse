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