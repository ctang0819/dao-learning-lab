# 逐步推理

## 1. 先确定可信业务状态

“医生提交医嘱”不表示下游可以执行。最小状态链可以是：

```text
DRAFT -> PENDING_REVIEW -> APPROVED -> DISPATCHED -> EXECUTING -> COMPLETED
                         \-> REJECTED
APPROVED / DISPATCHED / EXECUTING -> STOPPED
```

只有 `APPROVED` 表示业务上具备推进下游流程的资格；`DISPATCHED` 表示相关待办已经实际生成。两者必须分开，才能识别“审核通过了，但系统尚未生成待办”的故障窗口。

## 2. 为什么不能直接在事务外发送 MQ

若先提交医嘱审核通过、再发送 MQ，中间宕机会造成：医嘱已经是 `APPROVED`，但下游永远不知道它需要创建待办。

因此在同一个数据库事务中同时做两件事：

```text
医嘱状态更新为 APPROVED，版本变为 V
+ 写入 Outbox 事件（order_id、version、event_type、payload、status=NEW）
```

事务提交后，独立投递器扫描并重试 `NEW` 事件。这样“医嘱变更”和“待投递事件存在”要么都成功，要么都失败。

## 3. 为什么下游仍必须幂等

投递器可能已把消息发送至 MQ，却在将 Outbox 标记为 `SENT` 前宕机。恢复后会再次发送，因此下游必须接受至少一次投递。

同一版本的重复事件不能重复创建摆药、执行或收费待办。下游应以 `order_id + version + action_type` 标识同一版业务动作，并用唯一约束或条件更新实现幂等。

## 4. 为什么需要版本

虚拟医嘱 `O-100` 的版本 1 审核通过后，医生可修改或停止它，产生版本 2。版本 2 的停止事件可能先到，版本 1 的审核通过事件可能因延迟后到。

下游保存每条医嘱的最高已处理版本：

```text
incoming_version > processed_version  -> 处理新变化，并更新待办
incoming_version <= processed_version -> 视为重复或旧事件，忽略
```

版本比较与待办更新必须在同一原子操作内完成，避免两个 worker 并发时旧版本覆盖新版本。

## 5. 为什么仍要补偿与审计

消息系统不提供完整的医疗业务正确性。需要保留审计记录，并执行对账或补偿流程，覆盖事件漏投、消费失败、跨系统延迟、人工撤销与重试。
