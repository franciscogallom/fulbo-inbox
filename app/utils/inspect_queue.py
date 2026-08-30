# inspect_queue.py — script de debug

from redis import Redis
from rq import Queue
from rq.job import Job

redis_conn = Redis.from_url("redis://localhost:6379/0")
queue = Queue("wsp_messages", connection=redis_conn)

print(f"Mensajes pendientes: {len(queue)}")

for job_id in queue.job_ids:
    job = Job.fetch(job_id, connection=redis_conn)
    print(f"\nJob {job.id}")
    print(f"  args: {job.args}")
    print(f"  kwargs: {job.kwargs}")
    print(f"  status: {job.get_status()}")