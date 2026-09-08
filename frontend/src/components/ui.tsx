import type {ReactNode} from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import {X, ArrowUpRight, LoaderCircle} from 'lucide-react';
import type {Item} from '../api';
export function Status({value}:{value:string}){return <span className={`status ${value?.replaceAll(' ','-')}`}><i/>{value?.replaceAll('_',' ')}</span>}
export function ProjectIcon({project}:{project:Item}){return <span className="project-icon" style={{color:project.color,background:`${project.color}15`}}>{project.name?.slice(0,1)}</span>}
export function Panel({title,subtitle,action,children,className=''}:{title?:ReactNode;subtitle?:string;action?:ReactNode;children:ReactNode;className?:string}){return <section className={`panel ${className}`}>{title&&<div className="panel-head"><div><h3>{title}</h3>{subtitle&&<p>{subtitle}</p>}</div>{action}</div>}{children}</section>}
export function Empty({title='Nothing here yet',text='Connect your projects to get started.'}:{title?:string;text?:string}){return <div className="empty"><span>◎</span><h3>{title}</h3><p>{text}</p></div>}
export function Modal({open,onClose,title,description,children}:{open:boolean;onClose:()=>void;title:string;description?:string;children:ReactNode}){return <Dialog.Root open={open} onOpenChange={v=>!v&&onClose()}><Dialog.Portal><Dialog.Overlay className="overlay"/><Dialog.Content className="modal"><div className="modal-title"><Dialog.Title>{title}</Dialog.Title><Dialog.Close className="icon-button" aria-label="Close dialog"><X size={20}/></Dialog.Close></div><Dialog.Description className="muted">{description||'Configure this action for your workspace.'}</Dialog.Description>{children}</Dialog.Content></Dialog.Portal></Dialog.Root>}
export function ErrorNotice({error}:{error:Error|null}){return error?<div role="alert" className="error-notice">{error.message}</div>:null}
export function Submit({pending,children}:{pending:boolean;children:ReactNode}){return <button type="submit" className="button primary" disabled={pending}>{pending?<LoaderCircle size={16} className="spin"/>:null}{children}</button>}
export function PageTitle({title,description,action}:{title:string;description:string;action?:ReactNode}){return <div className="page-title"><div><h1>{title}</h1><p>{description}</p></div>{action}</div>}
export function External({href,children}:{href:string;children:ReactNode}){return <a href={href} target="_blank" rel="noreferrer" className="external">{children}<ArrowUpRight size={14}/></a>}
