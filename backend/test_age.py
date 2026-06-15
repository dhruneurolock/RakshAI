import psycopg2

try:
    conn = psycopg2.connect('postgresql://neuropent:neuropent_graph_pass@127.0.0.1:5433/neuropent_graph')
    with conn.cursor() as cur:
        cur.execute("LOAD 'age';")
        cur.execute("SET search_path = ag_catalog, \"$user\", public;")
        try:
            cur.execute("SELECT create_graph('neuropent_graph');")
            conn.commit()
            print('Graph created!')
        except Exception as e:
            conn.rollback()
            print('Graph exists:', e)
    print('Connection OK')
except Exception as e:
    print('Error:', e)
