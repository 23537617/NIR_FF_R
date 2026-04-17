import { Context, Contract, Info, Returns, Transaction } from 'fabric-contract-api';
import { Task, DocumentVersion } from './models';

const STATE_TRANSITIONS: Record<string, string[]> = {
    'NEW': ['IN_PROGRESS'],
    'IN_PROGRESS': ['REVIEW', 'NEW'],
    'REVIEW': ['CLOSED', 'IN_PROGRESS'],
    'CLOSED': []
};

@Info({ title: 'TaskDocumentChaincode', description: 'Smart contract for managing tasks and documents' })
export class TaskDocumentContract extends Contract {

    constructor() {
        super('TaskDocumentContract');
    }

    @Transaction(false)
    public async ping(ctx: Context): Promise<string> {
        return 'pong';
    }

    @Transaction()
    public async create_task(
        ctx: Context,
        task_id: string,
        title: string,
        description: string,
        assignee: string,
        creator: string
    ): Promise<string> {
        const exists = await this.taskExists(ctx, task_id);
        if (exists) {
            throw new Error(`The task ${task_id} already exists`);
        }

        const mspId = ctx.clientIdentity.getMSPID();
        const clientId = ctx.clientIdentity.getID();
        const creator_identity = `${mspId}:${clientId}`;

        const txTimestamp = ctx.stub.getTxTimestamp();
        let created_at = 'unknown';
        if (txTimestamp) {
            created_at = new Date(txTimestamp.seconds.low * 1000).toISOString();
        }

        const task: Task = {
            docType: 'task',
            task_id,
            title,
            description,
            assignee,
            status: 'NEW',
            created_at,
            creator_identity,
            documents: [],
            approvals: []
        };

        await ctx.stub.putState(`TASK_${task_id}`, Buffer.from(JSON.stringify(task)));

        ctx.stub.setEvent('onTaskCreated', Buffer.from(JSON.stringify(task)));

        return JSON.stringify({ success: true, message: `Task ${task_id} created`, task });
    }

    @Transaction(false)
    public async get_task(ctx: Context, task_id: string): Promise<string> {
        const taskBytes = await ctx.stub.getState(`TASK_${task_id}`);
        if (!taskBytes || taskBytes.length === 0) {
            throw new Error(`The task ${task_id} does not exist`);
        }
        return JSON.stringify({ success: true, data: JSON.parse(taskBytes.toString()) });
    }

    @Transaction(false)
    public async taskExists(ctx: Context, task_id: string): Promise<boolean> {
        const taskBytes = await ctx.stub.getState(`TASK_${task_id}`);
        return taskBytes && taskBytes.length > 0;
    }

    @Transaction()
    public async update_task_status(ctx: Context, task_id: string, new_status: string, updated_by: string): Promise<string> {
        const taskBytes = await ctx.stub.getState(`TASK_${task_id}`);
        if (!taskBytes || taskBytes.length === 0) {
            throw new Error(`The task ${task_id} does not exist`);
        }

        const task: Task = JSON.parse(taskBytes.toString());
        const old_status = task.status;
        
        // 1. Check State Machine transitions
        const allowedTransitions = STATE_TRANSITIONS[old_status] || [];
        if (!allowedTransitions.includes(new_status)) {
            throw new Error(`Invalid status transition from ${old_status} to ${new_status}`);
        }

        // 2. Enforce RBAC & Consensus for CLOSED
        if (new_status === 'CLOSED') {
            const mspId = ctx.clientIdentity.getMSPID();
            const id = ctx.clientIdentity.getID();
            
            // Checking RBAC (Admin from Org2)
            if (mspId !== 'Org2MSP' || (!id.includes('Admin') && !id.includes('admin'))) {
                throw new Error('Only Admin from Org2 can close a task');
            }
            
            // Checking Consensus (approvals from both Org1 and Org2)
            const approvals = task.approvals || [];
            if (!approvals.includes('Org1MSP') || !approvals.includes('Org2MSP')) {
                throw new Error('Cannot close task. Missing required approvals from both Org1 and Org2');
            }
        }

        task.status = new_status;

        await ctx.stub.putState(`TASK_${task_id}`, Buffer.from(JSON.stringify(task)));

        const txTimestamp = ctx.stub.getTxTimestamp();
        let timestamp = 'unknown';
        if (txTimestamp) {
            timestamp = new Date(txTimestamp.seconds.low * 1000).toISOString();
        }

        const eventPayload = {
            task_id,
            old_status,
            new_status,
            updated_by,
            timestamp
        };
        ctx.stub.setEvent('onTaskStatusUpdated', Buffer.from(JSON.stringify(eventPayload)));

        return JSON.stringify({ success: true, message: `Task ${task_id} status updated to ${new_status}`, task });
    }

    @Transaction()
    public async approve_task(ctx: Context, task_id: string): Promise<string> {
        const taskBytes = await ctx.stub.getState(`TASK_${task_id}`);
        if (!taskBytes || taskBytes.length === 0) {
            throw new Error(`The task ${task_id} does not exist`);
        }

        const task: Task = JSON.parse(taskBytes.toString());
        const mspId = ctx.clientIdentity.getMSPID();

        if (!task.approvals) {
            task.approvals = [];
        }

        if (!task.approvals.includes(mspId)) {
            task.approvals.push(mspId);
            await ctx.stub.putState(`TASK_${task_id}`, Buffer.from(JSON.stringify(task)));
            
            ctx.stub.setEvent('onTaskApproved', Buffer.from(JSON.stringify({ task_id, approved_by_msp: mspId })));
            return JSON.stringify({ success: true, message: `Task ${task_id} approved by ${mspId}` });
        }

        return JSON.stringify({ success: true, message: `Task ${task_id} was already approved by ${mspId}` });
    }

    @Transaction()
    public async add_document_version(
        ctx: Context,
        task_id: string,
        document_id: string,
        version: string,
        content_hash: string,
        uploaded_by: string,
        metadata?: string
    ): Promise<string> {
        const taskBytes = await ctx.stub.getState(`TASK_${task_id}`);
        if (!taskBytes || taskBytes.length === 0) {
            throw new Error(`The task ${task_id} does not exist`);
        }
        const task: Task = JSON.parse(taskBytes.toString());

        const compositeKey = ctx.stub.createCompositeKey('Task-Doc-Version', [task_id, document_id, version]);
        const exists = await ctx.stub.getState(compositeKey);
        if (exists && exists.length > 0) {
            throw new Error(`Version ${version} of document ${document_id} already exists for task ${task_id}`);
        }

        const txTimestamp = ctx.stub.getTxTimestamp();
        let uploaded_at = 'unknown';
        if (txTimestamp) {
            uploaded_at = new Date(txTimestamp.seconds.low * 1000).toISOString();
        }

        const docVersion: DocumentVersion = {
            docType: 'document_version',
            document_id,
            version,
            content_hash,
            uploaded_at,
            uploaded_by,
            metadata: metadata || '{}'
        };

        await ctx.stub.putState(compositeKey, Buffer.from(JSON.stringify(docVersion)));

        if (!task.documents) {
            task.documents = [];
        }
        if (!task.documents.includes(document_id)) {
            task.documents.push(document_id);
            await ctx.stub.putState(`TASK_${task_id}`, Buffer.from(JSON.stringify(task)));
        }

        const eventPayload = {
            task_id,
            document_id,
            version,
            uploaded_by
        };
        ctx.stub.setEvent('onDocumentVersionAdded', Buffer.from(JSON.stringify(eventPayload)));

        return JSON.stringify({ success: true, message: `Document version added to task ${task_id}`, document: docVersion });
    }

    @Transaction(false)
    public async get_document_versions(ctx: Context, task_id: string, document_id: string): Promise<string> {
        const iterator = await ctx.stub.getStateByPartialCompositeKey('Task-Doc-Version', [task_id, document_id]);
        const allResults = [];
        let result = await iterator.next();
        while (!result.done) {
            const strValue = Buffer.from(result.value.value).toString('utf8');
            let record;
            try {
                record = JSON.parse(strValue);
            } catch (err) {
                record = strValue;
            }
            allResults.push(record);
            result = await iterator.next();
        }
        await iterator.close();
        return JSON.stringify({ success: true, data: allResults });
    }

    @Transaction(false)
    public async get_task_history(ctx: Context, task_id: string): Promise<string> {
        const iterator = await ctx.stub.getHistoryForKey(`TASK_${task_id}`);
        const allResults = [];
        let result = await iterator.next();
        while (!result.done) {
            const strValue = Buffer.from(result.value.value).toString('utf8');
            let record;
            if (strValue) {
                try {
                    record = JSON.parse(strValue);
                } catch (err) {
                    record = strValue;
                }
            } else {
                record = 'DELETE'; // This is a delete transaction
            }

            allResults.push({
                tx_id: result.value.txId,
                timestamp: result.value.timestamp,
                is_delete: result.value.isDelete,
                value: record
            });
            result = await iterator.next();
        }
        await iterator.close();
        return JSON.stringify({ success: true, data: allResults });
    }

    @Transaction(false)
    public async query_tasks(ctx: Context, query_string: string, page_size?: number, bookmark?: string): Promise<string> {
        let qs = query_string;
        if (!qs) {
            qs = '{"selector":{"docType":"task"}}';
        }

        if (page_size && Number(page_size) > 0) {
            const iterator = await ctx.stub.getQueryResultWithPagination(qs, Number(page_size), bookmark || '');
            const allResults = [];
            let result = await iterator.iterator.next();
            while (!result.done) {
                const strValue = Buffer.from(result.value.value).toString('utf8');
                let record;
                try {
                    record = JSON.parse(strValue);
                } catch (err) {
                    record = strValue;
                }
                allResults.push(record);
                result = await iterator.iterator.next();
            }
            const returnMeta = {
                fetched_records_count: iterator.metadata.fetchedRecordsCount,
                bookmark: iterator.metadata.bookmark
            };
            await iterator.iterator.close();
            return JSON.stringify({ success: true, data: allResults, metadata: returnMeta });
        } else {
            const iterator = await ctx.stub.getQueryResult(qs);
            const allResults = [];
            let result = await iterator.next();
            while (!result.done) {
                const strValue = Buffer.from(result.value.value).toString('utf8');
                let record;
                try {
                    record = JSON.parse(strValue);
                } catch (err) {
                    record = strValue;
                }
                allResults.push(record);
                result = await iterator.next();
            }
            await iterator.close();
            return JSON.stringify({ success: true, data: allResults });
        }
    }
}
