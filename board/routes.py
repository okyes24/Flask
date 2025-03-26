from flask import Flask, render_template
from flask import request, redirect, url_for
import cx_Oracle

from . import board_bp

# 오라클 DB 연동하기
def  get_db_connection():
    dsn = cx_Oracle.makedsn('localhost','1521', service_name='XE')
    connection = cx_Oracle.connect(user='majustory',password='1234', dsn=dsn)
    return connection

@board_bp.route('/board_delete')
def  board_delete():
    print("===> board_delete ")
    # GET 방법으로 값 받아오기
    idx = request.args.get("idx")
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
                   delete from board where idx = :1
                   """
                   , (idx,))

    connection.commit()
    cursor.close()
    connection.close()

    return redirect(url_for('board_bp.board_list'))



@board_bp.route('/board_update', methods=['post'])
def board_update():
  idx = request.form['idx']
  sname = request.form['sname']
  title = request.form['title']
  content = request.form['content']

  connection = get_db_connection()
  cursor = connection.cursor()
  cursor.execute(
      '''
         update board 
         set sname =:1, title =:2, content=:3 
         where idx=:4          
      ''',(sname, title,content, idx)
  )
  connection.commit()
  cursor.close()
  connection.close()
  return redirect(url_for('board_bp.board_list'))

@board_bp.route("/board_save", methods=['post'])
def board_save():
    sname = request.form['sname']
    title = request.form['title']
    content = request.form['content']
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
          '''
             insert into board(idx, sname, title, content,cnt)
             values(idx_board.nextval, :1, :2,:3, 0)
          ''',(sname, title,content)
    )
    connection.commit()
    cursor.close()
    connection.close()
    # url_for('board_bp.board_list') 는 함수 이름을 찾는다.
    return redirect(url_for('board_bp.board_list'))

@board_bp.route("/board_form")
def board_form():
    return render_template('board/form.html')



@board_bp.route("/board_edit")
def  board_edit():
    # GET 방법으로 값 받아오기
    idx = request.args.get("idx")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        '''
           update board 
           set cnt = cnt + 1
           where idx=:1          
        ''', (idx,)
    )
    connection.commit()

    cursor.execute("""
                   select * from board where idx = :1
                   """
                   , (idx,))
    row = cursor.fetchone()

    # 튜플값을 딕셔너리로 변경해서 컬럼이름을 사용할 수 있도록 도와준다.
    if row :
        column_names = [desc[0].lower() for desc in cursor.description]
        result = dict(zip(column_names, row))

        return  render_template('board/edit.html' , row= result )

    cursor.close()
    connection.close()

@board_bp.route("/board_insert")
def board_insert():

    from faker import Faker
    fake = Faker('ko-KR')
    """
    fake.address(): 한국 주소 형식을 생성합니다.
    fake.company(): 한국 회사명을 생성합니다.
    fake.job(): 한국 직업명을 생성합니다.
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    for  i in range(100):
        sname = fake.name()
        title = fake.company()
        content = fake.text()
        cursor.execute(
              '''
                 insert into board(idx, sname, title, content,cnt)
                 values(idx_board.nextval, :1, :2,:3, 0)
              ''',(sname, title,content)
        )
        connection.commit()
    cursor.close()
    connection.close()
    # url_for('board_bp.board_list') 는 함수 이름을 찾는다.
    return redirect(url_for('board_bp.board_list'))

@board_bp.route("/board_list")
def board_list():
    ch1 = request.args.get("ch1")
    ch2 = request.args.get("ch2")
    print(ch1,ch2)
    import math
    connection = get_db_connection()
    cursor = connection.cursor()
    start_idx = request.args.get("start_idx")
    page_size= 10

    if start_idx is None:
        start_idx = 1
    else:
        start_idx=int(request.args.get("start_idx"))

    # cursor.execute(""" select idx, sname, title, cnt from board order by idx asc
    #     OFFSET :1 ROW FETCH NEXT :2 ROWS ONLY """,(start_idx,page_size,))
    if ch1 is None:
        cursor.execute(""" select ROWNUM , K.* from (  select rownum as rnum , P.*  from(select  idx,  sname,  title,  cnt  from  board  order  by idx ) P
               where ROWNUM <= :1 ) K 
            where rnum >= :2  
            """, (start_idx + page_size - 1, start_idx,))
    else:
        if ch1 == 'sname':
            cursor.execute(f""" select ROWNUM , K.* from (  select rownum as rnum , P.*  from(select  idx,  sname,  title,  cnt  from  board  
            where sname like :1
            order  by idx ) P
                   where ROWNUM <= :2 ) K 
                where rnum >= :3  
                """, ('%'+ch2+'%',start_idx + page_size - 1, start_idx,))
        else:
            cursor.execute(f""" select ROWNUM , K.* from (  select rownum as rnum , P.*  from(select  idx,  sname,  title,  cnt  from  board  
            where title like :1
            order  by idx ) P
                   where ROWNUM <= :2 ) K 
                where rnum >= :3  
                """, ('%'+ch2+'%',start_idx + page_size - 1, start_idx,))


    # 튜플값을 딕셔너리로 변경해서 컬럼이름을 사용할 수 있도록 도와준다.
    column_names = [desc[0].lower() for desc in cursor.description]
    rows = [dict(zip(column_names, row)) for row in cursor.fetchall()]

    if ch1 is None:
        cursor.execute(""" select count(*) tc from board
                """)
    else:
        cursor.execute(f""" select count(*) tc from board where {ch1} like :1
            """,('%'+ch2+'%',))
    total_count=cursor.fetchall()
    total_count=total_count[0][0]
    total_page=math.ceil(total_count / page_size)
    now_page=int(start_idx / page_size) + 1

    cursor.close()
    connection.close()
    return render_template('board/list.html',
                           rows=rows, total_count=total_count,
                           start_idx=start_idx,total_page=total_page,
                           now_page=now_page,
                           page_size=page_size,)