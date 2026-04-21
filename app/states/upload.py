import reflex as rx
import asyncio
import random
from datetime import datetime
from typing import TypedDict


class UploadJob(TypedDict):
    id: str
    match_name: str
    filename: str
    file_size: str
    status: str
    upload_time: str
    progress: int
    players_tracked: int
    events_detected: int
    duration: str


class UploadState(rx.State):
    jobs: list[UploadJob] = [
        {
            "id": "1",
            "match_name": "Arsenal vs Chelsea - Premier League",
            "filename": "ars_che_full.mp4",
            "file_size": "1.2 GB",
            "status": "Complete",
            "upload_time": "2024-05-10 14:30",
            "progress": 100,
            "players_tracked": 22,
            "events_detected": 1452,
            "duration": "94:12",
        },
        {
            "id": "2",
            "match_name": "Barcelona vs Real Madrid - La Liga",
            "filename": "el_clasico_hd.mov",
            "file_size": "2.8 GB",
            "status": "Processing",
            "upload_time": "2024-05-11 09:15",
            "progress": 45,
            "players_tracked": 0,
            "events_detected": 0,
            "duration": "90:00",
        },
        {
            "id": "3",
            "match_name": "Liverpool vs Man City - PL",
            "filename": "liv_mci.mkv",
            "file_size": "950 MB",
            "status": "Queued",
            "upload_time": "2024-05-11 10:05",
            "progress": 0,
            "players_tracked": 0,
            "events_detected": 0,
            "duration": "98:30",
        },
        {
            "id": "4",
            "match_name": "Bayern vs Dortmund - Bundesliga",
            "filename": "der_klassiker.mp4",
            "file_size": "1.5 GB",
            "status": "Failed",
            "upload_time": "2024-05-09 18:20",
            "progress": 12,
            "players_tracked": 0,
            "events_detected": 0,
            "duration": "90:00",
        },
    ]
    uploading_files: list[str] = []
    search_query: str = ""
    filter_status: str = "All"

    @rx.var
    def filtered_jobs(self) -> list[UploadJob]:
        jobs = sorted(self.jobs, key=lambda x: x["upload_time"], reverse=True)
        if self.search_query:
            jobs = [
                j for j in jobs if self.search_query.lower() in j["match_name"].lower()
            ]
        if self.filter_status != "All":
            jobs = [j for j in jobs if j["status"] == self.filter_status]
        return jobs

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        for file in files:
            job_id = str(random.randint(1000, 9999))
            new_job: UploadJob = {
                "id": job_id,
                "match_name": file.name.split(".")[0].replace("_", " ").title(),
                "filename": file.name,
                "file_size": f"{random.randint(500, 2000)} MB",
                "status": "Processing",
                "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "progress": 0,
                "players_tracked": 0,
                "events_detected": 0,
                "duration": "90:00",
            }
            self.jobs.append(new_job)
            yield rx.toast(
                f"Successfully uploaded {file.name}. Analysis started.",
                close_button=True,
            )
            yield UploadState.simulate_processing(job_id)

    @rx.event(background=True)
    async def simulate_processing(self, job_id: str):
        while True:
            await asyncio.sleep(random.uniform(1.0, 2.0))
            async with self:
                job_index = next(
                    (i for i, j in enumerate(self.jobs) if j["id"] == job_id), -1
                )
                if job_index == -1:
                    return
                job = self.jobs[job_index]
                if job["status"] != "Processing":
                    return
                new_progress = min(100, job["progress"] + random.randint(5, 15))
                self.jobs[job_index]["progress"] = new_progress
                if new_progress in [25, 30, 35] and job["progress"] < 25:
                    yield rx.toast(f"{job['match_name']} analysis 25% complete")
                elif new_progress in [50, 55, 60] and job["progress"] < 50:
                    yield rx.toast(f"{job['match_name']} analysis 50% complete")
                elif new_progress in [75, 80, 85] and job["progress"] < 75:
                    yield rx.toast(f"{job['match_name']} analysis 75% complete")
                if new_progress >= 100:
                    self.jobs[job_index]["status"] = "Complete"
                    self.jobs[job_index]["players_tracked"] = random.randint(20, 22)
                    self.jobs[job_index]["events_detected"] = random.randint(800, 1500)
                    yield rx.toast(f"Analysis complete for {job['match_name']}!")
                    return

    @rx.event
    def retry_job(self, job_id: str):
        for i, job in enumerate(self.jobs):
            if job["id"] == job_id:
                self.jobs[i]["status"] = "Processing"
                self.jobs[i]["progress"] = 0
                yield rx.toast("Retrying analysis...")
                yield UploadState.simulate_processing(job_id)
                break

    @rx.event
    def cancel_job(self, job_id: str):
        self.jobs = [j for j in self.jobs if j["id"] != job_id]
        yield rx.toast("Analysis job cancelled.")

    @rx.event
    def clear_completed(self):
        self.jobs = [j for j in self.jobs if j["status"] != "Complete"]