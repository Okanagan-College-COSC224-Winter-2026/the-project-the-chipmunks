import { useEffect, useState } from "react";
import {
  createGroup,
  getNextGroupID,
  getUserId,
  listCourseMembers,
  listGroupMembers,
  listAllGroups,
  listStuGroup,
  listUnassignedGroups,
  saveGroups,
  deleteGroup,
  getAssignment,
} from "../util/api";
import { useParams } from "react-router-dom";
import "./Group.css";
import TabNavigation from "../components/TabNavigation";
import StatusMessage from "../components/StatusMessage";
import { isTeacher } from "../util/login";
import Textbox from "../components/Textbox";
import GroupChat from "../components/GroupChat";

function fisherYates<T>(array: T[]): T[] {
  let m = array.length, t, i;

  while (m) {
    i = Math.floor(Math.random() * m--);

    t = array[m];
    array[m] = array[i];
    array[i] = t;
  }

  return array;
}

export default function Group() {
  const { id } = useParams();
  const [classMembers, setclassMembers] = useState<User[]>([]);
  const [stuGroup, setStuGroup] = useState<StudentGroups[]>([]);
  const [groups, setGroups] = useState<CourseGroup[]>([]);
  const [groupTable, setGroupTable] = useState<GroupTable>({});
  const [selectedGroup, setSelectedGroup] = useState<number>(-1);
  const [memberTable, setMemberTable] = useState<GroupTable>({});
  const [groupName, setGroupName] = useState('');
  const [statusMessage, setStatusMessage] = useState('');
  const [statusType, setStatusType] = useState<'error' | 'success'>('error');
  const [stuId, setStuId] = useState<number>(0);

  const nameFromId = (id: number) => {
    return classMembers.find((mem) => mem.id === id)?.name || 'N/A';
  };

  const randomize = () => {
    const members = []

    for (const group of Object.values(groupTable)) {
      for (const member of group) {
        const n = { ...member }
        n.groupID = -1
        members.push(n)
      }
    }

    if (memberTable[-1]) {
      for (const member of memberTable[-1]) {
        const n = { ...member }
        n.groupID = -1
        members.push(n)
      }
    }

    const membersPerGroup = members.length / Object.keys(groupTable).length
    const gIds = Object.keys(groupTable)
    const shuffled = fisherYates(members)
    const newTable: GroupTable = {}

    let i = 0
    for (const group of gIds) {
      for (let j = 0; j < membersPerGroup; j++) {
        const g = Number(group)
        const member = shuffled[i]
        i++

        if (!member) break

        const n = { ...member }
        n.groupID = Number(group)

        newTable[g] = newTable[g] || []
        newTable[g].push(n)
      }
    }

    setGroupTable(newTable)
    setMemberTable({})
  }

  useEffect(() => {
    (async () => {
      // Resolve the courseID from the assignment so we can fetch class members by class
      let courseId: string = String(id); // fallback
      try {
        const assignment = await getAssignment(Number(id));
        if (assignment && assignment.courseID) {
          courseId = String(assignment.courseID);
        }
      } catch {
        // If we can't resolve, members may be empty
      }

      const classMembers = await listCourseMembers(courseId);
      setclassMembers(classMembers);
      const groups = await listAllGroups(Number(id));
      setGroups(groups);
      const ua = await listUnassignedGroups(Number(id));
      const stuId = await getUserId();
      setStuId(stuId);
      const stus = await listStuGroup(Number(id), stuId);
      setStuGroup(stus);

      const groupMembers: {
        [key: number]: GroupTableValue[];
      } = {};
      for (const g of groups) {
        const members = await listGroupMembers(Number(id), g.id);
        groupMembers[g.id] = members;
      }

      const grLocal: GroupTable = {};
      for (const gr of groups) {
        grLocal[gr.id] = [];
        for (const stu of groupMembers[gr.id]) {
          if (stu.groupID === gr.id) {
            grLocal[gr.id].push(stu);
          }
        }
      }
      setGroupTable(grLocal);

      const memLocal: GroupTable = {};
      memLocal[-1] = [];
      for (const stu of ua) {
        memLocal[-1].push(stu);
      }
      setMemberTable(memLocal);
    })();
  }, [id]);

  return (
    <>
      <div className="AssignmentHeader">
        <h2>Assignment {id}</h2>
      </div>

      <TabNavigation
        tabs={[
          {
            label: "Home",
            path: `/assignments/${id}`,
          },
          {
            label: "Group",
            path: `/assignments/${id}/group`,
          }
        ]}
      />

      <StatusMessage message={statusMessage} type={statusType} />

      <div className="AssignmentPage">
        {isTeacher() ? (
          <>
            <div className="assignmentTables">
              <table className="table">
                <tbody>
                <tr>
                  <th>Unassigned</th>
                </tr>
                {memberTable[-1]
                  ? memberTable[-1].map((ua) => {
                      return (
                        <tr key={ua.userID}>
                          <span className="StudentName">{nameFromId(ua.userID)}</span>
                          <button
                            onClick={() => {
                              const localMember = { ...memberTable };
                              const localGroup = { ...groupTable };
                              const memObj = localMember[-1].find(
                                (mem) => ua.userID == mem.userID
                              );

                              if (memObj == undefined || selectedGroup == -1)
                                return;

                              localMember[-1] = localMember[-1].filter(
                                (g) => memObj?.userID != g.userID
                              );
                              memObj.groupID = selectedGroup;

                              if (memObj)
                                localGroup[selectedGroup].push(memObj);
                              else console.log("no unassigned users");

                              setMemberTable(localMember);
                              setGroupTable(localGroup);
                            }}
                          >
                            Move
                          </button>
                        </tr>
                      );
                    })
                  : null}
                </tbody>
              </table>

              <table className="table">
                <tbody>
                <tr>
                  <th>Groups</th>
                </tr>
                {Object.keys(groupTable).map((gId) => {
                  return (
                    <tr key={gId}>
                      <div
                        className={
                          "groupNames " +
                          (Number(gId) == selectedGroup ? "selected" : "")
                        }
                        onClick={() => setSelectedGroup(Number(gId))}
                      >
                        <div className="GroupArrow">
                          <img src="/icons/arrow.svg" alt="arrow" />
                        </div>
                        {groups.find((gr) => gr.id === Number(gId))?.name}
                      </div>

                      {selectedGroup !== -1 && selectedGroup == Number(gId)
                        ? groupTable[selectedGroup].map((stu) => {
                            return (
                              <div key={stu.userID} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                                <span className="StudentName">
                                  {nameFromId(stu.userID)}
                                </span>
                                <button
                                  onClick={() => {
                                    const localMember = { ...memberTable };
                                    const localGroup = { ...groupTable };
                                    const memObj = localGroup[
                                      selectedGroup
                                    ].find((mem) => stu.userID == mem.userID);

                                    if (memObj == undefined) return;

                                    localGroup[selectedGroup] = localGroup[
                                      selectedGroup
                                    ].filter((g) => memObj?.userID != g.userID);
                                    memObj.groupID = -1;

                                    if (memObj) localMember[-1].push(memObj);
                                    else console.log("shouldn't happen?");

                                    setMemberTable(localMember);
                                    setGroupTable(localGroup);
                                  }}
                                >
                                  Move
                                </button>
                              </div>
                            );
                          })
                        : null}
                    </tr>
                  );
                })}
                </tbody>
              </table>
            </div>
            <div>
            <button
              onClick={() => {
                const groupMems = Object.values(groupTable);
                const uaMems = Object.values(memberTable);
                for (const group of groupMems) {
                  for (const mem of group) {
                    saveGroups(mem.groupID, mem.userID, mem.assignmentID);
                  }
                }
                for (const group of uaMems) {
                  for (const mem of group) {
                    saveGroups(mem.groupID, mem.userID, mem.assignmentID);
                  }
                }

                setStatusType('success');
                setStatusMessage('Changes saved!');
              }}
            >
              Confirm Changes
            </button>

            <button
              style={{ backgroundColor: "var(--background-tertiary)" }}
              onClick={randomize}
            >
              Randomize
            </button>
            <button
              onClick={() => {
                if (selectedGroup == -1) return;
                const localGroup = { ...groupTable}
                delete localGroup[selectedGroup];
                setGroupTable(localGroup);
                deleteGroup(selectedGroup);
                setStatusType('success');
                setStatusMessage('Group deleted!');
              }}>
              Delete Selected Group
              </button>
            </div>

            <div>
              <button
                onClick={async () =>{
                  const nextGid = await getNextGroupID(Number(id));
                  const newId = Number(nextGid) + 1;
                  await createGroup(Number(id), groupName, newId);
                  // Reload groups
                  const updatedGroups = await listAllGroups(Number(id));
                  setGroups(updatedGroups);
                  const grLocal: GroupTable = { ...groupTable };
                  grLocal[newId] = [];
                  setGroupTable(grLocal);
                  setStatusType('success');
                  setStatusMessage(`Group "${groupName}" created!`);
                }}
                >
                  Create New Group
              </button>
              <Textbox
                placeholder="group name"
                onInput={setGroupName}
                className="groupNameInput"
                >
              </Textbox>
            </div>
          </>
        ) : (
          <div className="assignment">
            <table className="studentTable">
              <tbody>
              <tr>
                <th>My group</th>
              </tr>
              {stuGroup.map((stus) => {
                return <tr key={stus.userID}><td>{nameFromId(stus.userID)}</td></tr>;
              })}
              </tbody>
            </table>

            {/* Group chat — only shown when student has a group */}
            {stuGroup.length > 0 && (() => {
              const myGroupId = stuGroup[0].groupID;
              const otherMembers = stuGroup
                .filter(s => s.userID !== stuId)
                .map(s => ({ userId: s.userID, name: nameFromId(s.userID) }));
              const groupName = groups.find(g => g.id === myGroupId)?.name ?? 'Group Chat';
              return (
                <GroupChat
                  groupId={myGroupId}
                  groupName={groupName}
                  members={otherMembers}
                  currentUserId={stuId}
                />
              );
            })()}
          </div>
        )}
      </div>
    </>
  );
}