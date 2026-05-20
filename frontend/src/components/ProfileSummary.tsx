import type { StudentProfile } from '../api/profile'
import styles from './ProfileSummary.module.css'

export default function ProfileSummary({ profile }: { profile: StudentProfile }) {
  const ap = profile.academic_profile
  return (
    <div className={styles.card}>
      <div className={styles.row}>
        <div className={styles.avatar}>{profile.full_name[0]?.toUpperCase()}</div>
        <div className={styles.identity}>
          <p className={styles.name}>{profile.full_name}</p>
          <p className={styles.number}>{profile.student_number}</p>
        </div>
        <span
          className={`${styles.tag} ${
            profile.profile_source === 'ins_verified' ? styles.tagVerified : styles.tagManual
          }`}
        >
          {profile.profile_source === 'ins_verified' ? 'INS Verified' : 'Manual'}
        </span>
      </div>
      {ap && (
        <div className={styles.meta}>
          {ap.department_name && <span>{ap.department_name}</span>}
          {ap.major_name && <span>{ap.major_name}</span>}
          {ap.academic_year && <span>Year {ap.academic_year}</span>}
          {ap.current_gpa != null && profile.gpa_rules_enabled && (
            <span>GPA {ap.current_gpa.toFixed(2)}</span>
          )}
        </div>
      )}
    </div>
  )
}
